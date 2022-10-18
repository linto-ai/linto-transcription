""" The transcription_task module implements the transcription's task steps to be served by the request celery workers."""
import logging
import os
import time

from transcriptionservice.broker.celeryapp import celery
from transcriptionservice.server.mongodb.db_client import DBClient
from transcriptionservice.transcription.configs.transcriptionconfig import \
    TranscriptionConfig
from transcriptionservice.transcription.transcription_result import \
    TranscriptionResult
from transcriptionservice.transcription.utils.audio import (
    splitFile, splitUsingTimestamps, transcoding)
from transcriptionservice.transcription.utils.serviceresolve import (
    ResolveException, ServiceResolver)
from transcriptionservice.transcription.utils.taskprogression import (
    StepState, TaskProgression)

__all__ = ["transcription_task"]

# Create shared mongoclient
db_info = {
    "db_host": os.environ.get("MONGO_HOST", None),
    "db_port": int(os.environ.get("MONGO_PORT", None)),
    "service_name": os.environ.get("SERVICE_NAME", None),
    "db_name": "transcriptiondb",
}

language = os.environ.get("LANGUAGE", None)

db_client = DBClient(db_info)


@celery.task(name="transcription_task", bind=True)
def transcription_task(self, task_info: dict, file_path: str):
    """Transcription task processes a transcription request.

    task_info contains the following field:
    - "transcription_config" : Transcription configuration
    - "result_db" : Connexion info to the result database
    - "service": Name of the transcription service
    - "hash": Audio File Hash
    - "keep_audio": If False, the audio file is deleted after the task.
    - "timestamps" : (Optionnal) Audio spliting timestamps
    """
    # Logging task
    logging.basicConfig(
        filename=f"/usr/src/app/logs/{self.request.id}.txt",
        filemode="a",
        format="%(asctime)s,%(levelname)s %(message)s",
        datefmt="%H:%M:%S",
        level=logging.DEBUG,
        force=True,
    )

    logging.info(f"Running task {self.request.id}")

    self.update_state(state="STARTED", meta={"steps": {}})

    config = TranscriptionConfig(task_info["transcription_config"])

    # Disable diarization if timestamps are uploaded
    if task_info["timestamps"]:
        config.diarizationConfig.isEnabled = False
        logging.debug("Disabling diarization due to timestamps information")

    logging.info(config)

    # Resolve required task queues
    resolver = ServiceResolver()

    for task in config.tasks:
        try:
            resolver.resolve_task(task)
            logging.info(
                f"Task {task} successfuly resolved -> {task.serviceName}:{task.serviceQueue} (Policy={resolver.service_policy})"
            )
        except ResolveException as error:
            logging.error(str(error))
            raise ResolveException(f"Failed to resolve: {str(error)}")

    # Task progression
    progress = TaskProgression(
        [
            ("preprocessing", True),
            ("transcription", True),
            ("diarization", config.diarizationConfig.isEnabled),
            ("punctuation", config.punctuationConfig.isEnabled),
            ("postprocessing", True),
        ]
    )
    progress.steps["preprocessing"].state = StepState.STARTED
    self.update_state(state="STARTED", meta=progress.toDict())

    # Preprocessing
    ## Transtyping
    logging.info(f"Converting input file to wav.")
    file_name = transcoding(file_path)

    # Check for available transcription
    logging.info(f"Checking for available transcription")

    if not task_info["timestamps"]:
        available_transcription = db_client.fetch_transcription(task_info["hash"])
    else:
        available_transcription = None

    if available_transcription:
        logging.info("Transcription result already available")
        try:
            transcription_result = TranscriptionResult(None)
            transcription_result.setTranscription(available_transcription["words"])
            progress.steps["transcription"].state = StepState.DONE
            progress.steps["preprocessing"].state = StepState.DONE
        except Exception as e:
            logging.warning("Failed to fetch transcription: {}".format(str(e)))
            available_transcription = None
    self.update_state(state="STARTED", meta=progress.toDict())

    if available_transcription is None:
        # Split using VAD
        if not task_info["timestamps"]:
            logging.info(f"Spliting using VAD ...")
            subfiles, total_duration = splitFile(file_name)

        else:
            logging.info(f"Split using provided timestamps ...")
            subfiles, total_duration = splitUsingTimestamps(file_name, task_info["timestamps"])

        logging.info(f"Input file has been split into {len(subfiles)} subfiles")

        # Progress monitoring
        speakers = None
        progress.steps["preprocessing"].state = StepState.DONE
        self.update_state(state="STARTED", meta=progress.toDict())

        # Transcription
        transJobIds = []
        progress.steps["transcription"].state = StepState.STARTED
        for subfile_path, offset, duration in subfiles:
            transJobId = celery.send_task(
                name="transcribe_task",
                queue=task_info["service_name"],
                args=[subfile_path, True],
            )
            transJobIds.append((transJobId, offset, duration, subfile_path))

        self.update_state(state="STARTED", meta=progress.toDict())

    # Diarization (In parallel)
    if config.diarizationConfig.isEnabled:
        logging.info(f"Processing diarization task on {config.diarizationConfig.serviceQueue}...")
        progress.steps["diarization"].state = StepState.STARTED
        diarJobId = celery.send_task(
            name=config.diarizationConfig.task_name,
            queue=config.diarizationConfig.serviceQueue,
            args=[
                file_name,
                config.diarizationConfig.numberOfSpeaker,
                config.diarizationConfig.maxNumberOfSpeaker,
            ],
        )
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
            progress.steps["transcription"].progress += duration / total_duration
            self.update_state(state="STARTED", meta=progress.toDict())
        logging.info(f"Transcription task complete")
        progress.steps["transcription"].state = StepState.DONE

        self.update_state(state="STARTED", meta=progress.toDict())

        if failed:
            raise Exception("Transcription has failed: {}".format(transcription))

        # Merge Transcription results
        if task_info["timestamps"]:
            transcription_result = TranscriptionResult(
                transcriptions, [x["spk_id"] for x in task_info["timestamps"]]
            )
        else:
            transcription_result = TranscriptionResult(transcriptions)

        # Save transcription in DB
        try:
            db_client.push_transcription(task_info["hash"], transcription_result.words)
        except Exception as e:
            logging.warning("Failed to push transcription to DB: {}".format(e))

    # Diarization result
    if config.diarizationConfig.isEnabled:
        speakers = diarJobId.get(disable_sync_subtasks=False)
        progress.steps["diarization"].state = StepState.DONE
        self.update_state(state="STARTED", meta=progress.toDict())
        logging.info(f"Diarization task complete")
        if diarJobId.status == "FAILURE":
            raise Exception("Diarization has failed: {}".format(speakers))
        else:
            transcription_result.setDiarizationResult(speakers)
    elif not task_info["timestamps"]:
        transcription_result.setNoDiarization()

    # Punctuation
    if config.punctuationConfig.isEnabled:
        logging.info(f"Processing punctuation task on {config.punctuationConfig.serviceQueue} ...")
        progress.steps["punctuation"].state = StepState.STARTED
        self.update_state(state="STARTED", meta=progress.toDict())
        puncJobId = celery.send_task(
            name=config.punctuationConfig.task_name,
            queue=config.punctuationConfig.serviceQueue,
            args=[[seg.toString() for seg in transcription_result.segments]],
        )
        try:
            punctuated_text = puncJobId.get(disable_sync_subtasks=False)
            logging.info(f"Punctuation task complete.")
        except Exception as e:
            progress.steps["punctuation"].state = StepState.DONE
            logging.error(f"Punctuation task complete")
            raise Exception("Punctuation has failed: {}".format(str(e)))
        self.update_state(state="STARTED", meta=progress.toDict())
        transcription_result.setProcessedSegment(punctuated_text)

    logging.info(f"Task complete, post processing ...")
    # Write result in database
    progress.steps["postprocessing"].state = StepState.STARTED
    self.update_state(state="STARTED", meta=progress.toDict())
    try:
        result_id = db_client.push_result(
            file_hash=task_info["hash"],
            job_id=self.request.id,
            origin="origin",
            service_name=task_info["service_name"],
            config=config,
            result=transcription_result,
        )
    except Exception as e:
        raise Exception("Failed to process result")

    # Free ressource
    if not task_info["keep_audio"]:
        try:
            os.remove(file_name)
        except Exception as e:
            logging.warning("Failed to remove ressource {}".format(file_path))
    progress.steps["postprocessing"].state = StepState.DONE
    return result_id
