import os
import io
import requests
import time
import json

from pymongo import MongoClient

from transcriptionservice.workers.formating import clean_text, speakers_format
from transcriptionservice.workers.celeryapp import celery
from transcriptionservice.server.mongodb.mongotutils import check_for_result
from transcriptionservice.server.mongodb.db_client import DBClient

__all__ = ["diarization_task", "punctuation_task", "transcription_task"]

# Create shared mongoclient
db_info = {"db_host" : os.environ.get("MONGO_HOST", None),
           "db_port" : int(os.environ.get("MONGO_PORT", None)),
           "service_name" : os.environ.get("SERVICE_NAME", None),
           "db_name": "result_db"}
db_client = DBClient(db_info)

#@celery.task(name="diarization_task")
#def diarization_task(request_host, file_path):
#    """ diarization_task do a synchronous call to the diarization worker API """
#    result = requests.post(request_host, headers={"accept":"application/json"}, files={'file' : open(file_path, 'rb').read()})
#    if result.status_code == 200:
#        return json.loads(result.text)["segments"]
#    else:
#        raise Exception(result.text)



@celery.task(name="diarization_task")
def diarization_task(file_path, speaker_number):
    pass

#@celery.task(name="punctuation_task")
#def punctuation_task(request_host, text):
#    # Simple text
#    if type(text) is str:
#        result = requests.post(request_host, text.strip().encode('utf-8'), headers={'content-type': 'application/octet-stream'})
#        if result.status_code == 200:
#            return result.text
#        else:
#            raise Exception(result.text)
#    # List of utterance of format speaker: utterance
#    elif type(text) is list:
#        result_arr = []
#        for line in text:
#            spk, utterance = line.split(':')
#            result = requests.post(request_host, utterance.strip().encode('utf-8'), headers={'content-type': 'application/octet-stream'})
#            if result.status_code != 200:
#                raise Exception(result.text)
#            result_arr.append("{}: {}".format(spk, result.text))
#        return result_arr

@celery.task(name="punctuation_task")
def punctuation_task(text):
    pass

@celery.task(name="transcription_task", bind=True)
def transcription_task(self, task_info: dict, file_path: str):
    """ Transcription task processes a transcription request. 
    
    task_info contains the following field:
    - "format" : Expected output format.
    - "result_db" : Connexion info to the result database
    - "spk_number": Known number of speakers or None
    - "service": Name of the transcription service
    - "hash": Audio File Hash
    - "keep_audio": If False, the audio file is deleted after the task.
    """
    print(task_info)
    output_format = task_info["format"]
    file_name = os.path.basename(file_path)
    
    # Setup flags
    do_diarization = output_format in ["speakers", "formated"]
    do_punctuaction = output_format in ["text", "speakers", "formated"]

    # Check that required services are available # TODO test
    worker_list = celery.control.inspect().active_queues().keys()
    worker_names = set(k.split("@")[0] for k in worker_list)

    if not "{}_worker".format(task_info["service_name"]) in worker_names:
        raise Exception("No transcription service running for {}".format(task_info["service_name"]))
    
    if do_diarization and not "diarization_worker" in worker_names:
        raise Exception("Request required diarization but no diarization service is running.")

    if do_punctuaction and not "punctuation_worker" in worker_names:
        raise Exception("Request required punctuation but no punctuation service is running.")

    # Progress monitoring
    total_step = 4 + do_diarization + do_punctuaction
    current_step = 0
    speakers = None
    self.update_state(state="STARTED", meta={"current": current_step, "total": total_step, "step": "Transcription"})
    
    # Transcription
    transJobId = celery.send_task(name="transcribe_task", queue=task_info["service_name"], args=[file_name, output_format])

    # Diarization (In parallel)
    if do_diarization:
        diarJobId = celery.send_task(name="diarization_task", queue='diarization', args=[file_name, task_info["spk_number"]])
    transcription = transJobId.get(disable_sync_subtasks=False)
    
    if transJobId.status == "FAILURE":
        raise Exception("Transcription has failed: {}".format(transcription))

    current_step+=1
    if do_diarization:
        self.update_state(state="STARTED", meta={"current": current_step, "total": total_step, "step": "Diarization"})
        speakers = diarJobId.get(disable_sync_subtasks=False)
        if diarJobId.status == "FAILURE":
            raise Exception("Diarization has failed: {}".format(speakers))
        current_step += 1

    # Format response
    self.update_state(state="STARTED", meta={"current": current_step, "total": total_step, "step": "Post-Processing"})
    try:
        if output_format == "raw":
            formated_result = clean_text(transcription)
        elif output_format == "speakers":
            formated_result = speakers_format(transcription, speakers)
        elif output_format == "formated":
            formated_result = speakers_format(transcription, speakers)["text"]
    except Exception as e:
        raise Exception("Post-processing failure: {}".format(str(e)))
    current_step += 1

    # Punctuation 
    if do_punctuaction:
        self.update_state(state="STARTED", meta={"current": current_step, "total": total_step, "step": "Punctuation"})
        input_text = formated_result if output_format in ["text", "formated"] else formated_result["text"]
        puncJobId = celery.send_task(name="diarization_task", queue='diarization', args=[file_name, task_info["spk_number"]])
        puncJobId = punctuation_task.apply_async(queue='punctuation', args=[task_info["hosts"]["punctuation"], input_text])
        try: 
            punctuated_text = puncJobId.get(disable_sync_subtasks=False)
        except Exception as e:
            raise Exception("Punctuation has failed: {}".format(str(e)))
        current_step += 1

        if output_format in ["text", "formated"]:
            formated_result = punctuated_text
        else:
            formated_result["text"] = punctuated_text
    
    # Write result in database
    self.update_state(state="STARTED", meta={"current": current_step, "total": total_step, "step": "Cleaning"})
    try:
        db_client.write_result(task_info["hash"], output_format, formated_result)
    except Exception as e:
        print("Failed to write result in database")
    
    # Free ressource
    if not task_info["keep_audio"]:
        try:
            os.remove(file_path)
        except Exception as e:
            print("Failed to remove ressource {}".format(file_path))

    return {"result": formated_result}
