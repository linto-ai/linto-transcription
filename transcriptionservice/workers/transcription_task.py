import os
import io
import requests
import time
import json

from pymongo import MongoClient

from transcriptionservice.workers.audio import transcoding, splitFile
from transcriptionservice.workers.celeryapp import celery
from transcriptionservice.server.mongodb.db_client import DBClient
from transcriptionservice.workers.utils import TranscriptionConfig, TranscriptionResult, TaskProgression, StepState

__all__ = ["transcription_task"]

# Create shared mongoclient
db_info = {"db_host" : os.environ.get("MONGO_HOST", None),
           "db_port" : int(os.environ.get("MONGO_PORT", None)),
           "service_name" : os.environ.get("SERVICE_NAME", None),
           "db_name": "transcriptiondb"}

language = os.environ.get("LANGUAGE", None)
           
db_client = DBClient(db_info)

@celery.task(name="transcription_task", bind=True)
def transcription_task(self, task_info: dict, file_path: str):
    """ Transcription task processes a transcription request. 
    
    task_info contains the following field:
    - "transcription_config" : Transcription configuration
    - "result_db" : Connexion info to the result database
    - "service": Name of the transcription service
    - "hash": Audio File Hash
    - "keep_audio": If False, the audio file is deleted after the task.
    """
    self.update_state(state="STARTED", meta={"steps": {}})
    print(task_info)

    config = TranscriptionConfig(task_info["transcription_config"])

    # Setup flags
    do_diarization = config.diarizationConfig["enableDiarization"] and config.diarizationConfig["numberOfSpeaker"] != 1
    do_punctuation = config.enablePunctuation

    # Check that required services are available # TODO test
    worker_list = celery.control.inspect().active_queues().keys()
    worker_names = set(k.split("@")[0] for k in worker_list)

    if not "{}_worker".format(task_info["service_name"]) in worker_names:
        raise Exception("No transcription service running for {}".format(task_info["service_name"]))
    
    if do_diarization and not "diarization_worker" in worker_names:
        raise Exception("Request required diarization but no diarization service is running.")

    if do_punctuation and not f"punctuation_{language}" in worker_names:
        raise Exception("Request required punctuation but no punctuation service is running.")

    # Preprocessing
    # Transtyping
    file_name = transcoding(file_path)
    
    # Check for available transcription
    available_transcription = db_client.fetch_transcription(task_info["hash"])

    progress = TaskProgression([("preprocessing", True),
                                ("transcription", True),
                                ("diarization", do_diarization), 
                                ("punctuation", do_punctuation),
                                ("postprocessing", True)])
    
    progress.steps["preprocessing"].state = StepState.STARTED
    self.update_state(state="STARTED", meta=progress.toDict())

    if available_transcription:
        print('Transcription result already available')
        try:
            transcription_result = TranscriptionResult(None)
            transcription_result.setTranscription(available_transcription["words"])
            progress.steps["transcription"].state = StepState.DONE
            progress.steps["preprocessing"].state = StepState.DONE
        except Exception as e:
            print("Failed to fetch transcription: {}".format(str(e)))
            available_transcription = None
        

    self.update_state(state="STARTED", meta=progress.toDict())

    if available_transcription is None:
        # Split using VAD
        progress.steps["transcription"].state = StepState.STARTED
        subfiles, total_duration = splitFile(file_name)
        print(f'Input file has been split into {len(subfiles)} subfiles')

        # Progress monitoring
        speakers = None
        progress.steps["preprocessing"].state = StepState.DONE
        self.update_state(state="STARTED", meta=progress.toDict())
        
        # Transcription
        transJobIds = []
        progress.steps["transcription"].state = StepState.STARTED
        for subfile_path, offset, duration in subfiles:
            transJobId = celery.send_task(name="transcribe_task", queue=task_info["service_name"], args=[subfile_path, True])
            transJobIds.append((transJobId, offset, duration, subfile_path))
        
        self.update_state(state="STARTED", meta=progress.toDict())
    
    # Diarization (In parallel)
    if do_diarization:
        progress.steps["diarization"].state = StepState.STARTED
        diarJobId = celery.send_task(name="diarization_task",
                                     queue='diarization', 
                                     args=[file_name, 
                                           config.diarizationConfig["numberOfSpeaker"], 
                                           config.diarizationConfig["maxNumberOfSpeaker"]])
        self.update_state(state="STARTED", meta=progress.toDict())

    # Wait for all the transcription jobs
    if available_transcription is None:
        transcriptions = []
        pc_trans = 0.0
        failed = False
        for jobId, offset, duration, subfile_path in transJobIds:
            if failed:
                jobId.revoke()
                os.remove(subfile_path)
                continue
            transcription = jobId.get(disable_sync_subtasks=False)
            if len(transJobIds) > 1:
                os.remove(subfile_path)
            if jobId.status == "FAILURE":
                failed = True
                continue
            transcriptions.append((transcription, offset))
            progress.steps["transcription"].progress += (duration / total_duration)
            self.update_state(state="STARTED", meta=progress.toDict())
        progress.steps["transcription"].state = StepState.DONE
        
        self.update_state(state="STARTED", meta=progress.toDict())

        if failed:
            raise Exception("Transcription has failed: {}".format(transcription))

        # Merge Transcription results
        transcription_result = TranscriptionResult(transcriptions)

        # Save transcription in DB
        try:
            db_client.push_transcription(task_info["hash"], transcription_result.words)
        except Exception as e:
            print("Failed to push transcription to DB: {}".format(e))

    # Diarization result
    if do_diarization:
        self.update_state(state="STARTED", meta=progress.toDict())
        speakers = diarJobId.get(disable_sync_subtasks=False)
        progress.steps["diarization"].state = StepState.DONE
        self.update_state(state="STARTED", meta=progress.toDict())
        if diarJobId.status == "FAILURE":
            raise Exception("Diarization has failed: {}".format(speakers))
        else:
            transcription_result.setDiarizationResult(speakers)
    else:
        transcription_result.setNoDiarization()

    # Punctuation 
    if do_punctuation:
        progress.steps["punctuation"].state = StepState.STARTED
        self.update_state(state="STARTED", meta=progress.toDict())
        puncJobId = celery.send_task(name="punctuation_task", queue=f'punctuation_{language}', args=[[seg.toString() for seg in transcription_result.segments]])
        try: 
            punctuated_text = puncJobId.get(disable_sync_subtasks=False)
        except Exception as e:
            raise Exception("Punctuation has failed: {}".format(str(e)))
            progress.steps["punctuation"].state = StepState.DONE
        self.update_state(state="STARTED", meta=progress.toDict())
        transcription_result.setProcessedSegment(punctuated_text)

    # Write result in database
    progress.steps["postprocessing"].state = StepState.STARTED
    self.update_state(state="STARTED", meta=progress.toDict())
    try:
        result_id = db_client.push_result(file_hash=task_info["hash"], job_id=self.request.id, origin="origin", service_name=task_info["service_name"], config=config, result=transcription_result)
    except Exception as e:
        raise Exception("Failed to process result")
    
    # Free ressource
    if not task_info["keep_audio"]:
        try:
            os.remove(file_name)
        except Exception as e:
            print("Failed to remove ressource {}".format(file_path))
    progress.steps["postprocessing"].state = StepState.DONE
    return result_id