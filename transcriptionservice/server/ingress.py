#!/usr/bin/env python3
import os
import logging
import argparse

import celery
from celery.result import AsyncResult
from flask import Flask, request, abort, Response, json

from transcriptionservice.server.serving import GunicornServing
from transcriptionservice.workers.tasks import transcription_task
from transcriptionservice.server.confparser import createParser
from transcriptionservice.server.swagger import setupSwaggerUI
from transcriptionservice.server.utils import fileHash, requestlog
from transcriptionservice.server.utils.ressources import write_ressource
from transcriptionservice.server.mongodb.db_client import DBClient

AUDIO_FOLDER = "/opt/audio"

app = Flask("__services_manager__")

logging.basicConfig(format='%(asctime)s %(name)s %(levelname)s: %(message)s', datefmt='%d/%m/%Y %H:%M:%S')
logger = logging.getLogger("__services_manager__")

@app.route('/healthcheck', methods=["GET"])
def healthcheck():
    """ Server healthcheck """
    return "1", 200

@app.route('/job/<jobid>', methods=["GET"])
def jobstatus(jobid):
    task = AsyncResult(jobid)
    state = task.status
    if state == "STARTED":
        return json.dumps({"state": "started", "progress" : task.info}), 202
    elif state == "SUCCESS":
        result = task.get()
        return json.dumps({"state" : "done", "result": result["result"]}), 200
    elif state == "PENDING":
        return json.dumps({"state": "pending",}), 202
    elif state == "FAILURE":
        return json.dumps({"state": "failed", "reason": str(task.result)}), 400
    else:
        return "Task returned an unknown state", 400

@app.route('/transcribe', methods=["POST"])
def transcription():
    # Get file and generate hash
    if 'file' not in request.files.keys():
        return "Not file attached to request", 400
    
    file_buffer = request.files['file'].read()
    file_hash = fileHash(file_buffer)   

    # Expected return format
    output_format = request.form.get("format", "raw")
    logger.debug(request.form.keys())
    # Don't use cached result
    no_cache = request.form.get("no_cache", False) in [True, "True", "true", "1", 1]

    # If the number of speaker is specified
    spk_number = request.form.get("spk_number", None)

    # Check DATABASE for results
    logger.debug("is nocache: {}".format(no_cache))
    result = None
    if not no_cache:
        logger.debug("Check for cached result")
        result = db_client.check_for_result(file_hash,
                                            output_format)
    
    requestlog(logger, request.remote_addr, output_format, file_hash, result is not None)

    # If the result is cached returns previous result
    if result is not None:
        return json.dumps(result), 200

    # If no previous result
    # Create ressource
    try:
        file_path = write_ressource(file_buffer, file_hash, AUDIO_FOLDER)
    except Exception as e:
        logger.error("Failed to write ressource: {}".format(e))
        return "Server Error: Failed to write ressource", 500

    logger.debug("Create transcription task")

    task_info = {"format": output_format,
                 "spk_number" : spk_number, 
                 "service_name": config.service_name, 
                 "hash": file_hash, 
                 "keep_audio": config.keep_audio}
    
    task = transcription_task.apply_async(queue=config.service_name+'_requests', args=[task_info, file_path])

    return json.dumps({"jobid" : task.id}), 201

@app.route('/revoke/<jobid>', methods=["GET"])
def revoke(jobid):
    AsyncResult(jobid).revoke()
    return "done", 200
    
@app.errorhandler(405)
def method_not_allowed(error):
    return 'The method is not allowed for the requested URL', 405

@app.errorhandler(404)
def page_not_found(error):
    return 'The requested URL was not found', 404

@app.errorhandler(500)
def server_error(error):
    logger.error(error)
    return 'Server Error', 500

if __name__ == '__main__':
    parser = createParser() # Parser definition at server/utils/confparser.py

    config = parser.parse_args()
    logger.setLevel(logging.DEBUG if config.debug else logging.INFO)

    try:
        # Setup SwaggerUI
        if config.swagger_path is not None:
            setupSwaggerUI(app, config)
            logger.debug("Swagger UI set.")
    except Exception as e:
        logger.warning("Could not setup swagger: {}".format(str(e)))

    # Results database info
    db_info = {"db_host" : config.mongo_uri, 
               "db_port" : config.mongo_port, 
               "service_name" : config.service_name, 
               "db_name": "result_db"}
    
    db_client = DBClient(db_info)

    logger.info("Starting ingress")
    logger.debug(config)
    serving = GunicornServing(app, {'bind': '{}:{}'.format('0.0.0.0', 80),
                                    'workers': config.gunicorn_workers,})

    try:
        serving.run()
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
    finally:
        db_client.close()