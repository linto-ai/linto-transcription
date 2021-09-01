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

__all__ = ["transcription_task"]

# Create shared mongoclient
db_info = {"db_host" : os.environ.get("MONGO_HOST", None),
           "db_port" : int(os.environ.get("MONGO_PORT", None)),
           "service_name" : os.environ.get("SERVICE_NAME", None),
           "db_name": "result_db"}
           
db_client = DBClient(db_info)


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
    self.update_state(state="STARTED", meta={"current": 0, "total": 1, "step": "Started"})
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
        do_punctuaction = False
        #raise Exception("Request required punctuation but no punctuation service is running.")

    # Progress monitoring
    total_step = 4 + do_diarization + do_punctuaction
    current_step = 1
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
        if type(speakers) is str:
            speakers = json.loads(speakers)
        if diarJobId.status == "FAILURE":
            raise Exception("Diarization has failed: {}".format(speakers))
        current_step += 1

    # Format response
    self.update_state(state="STARTED", meta={"current": current_step, "total": total_step, "step": "Post-Processing"})
    try:
        if output_format == "raw":
            formated_result = clean_text(transcription)
        elif output_format == "speakers":
            print(type(speakers))
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
        puncJobId = celery.send_task(name="punctuation_task", queue='punctuation', args=[input_text, None if output_format == 'raw' else ':'])
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
