#!/usr/bin/env python3
import requests
import json
import time

INGRESS_HOST= "http://0.0.0.0:8000"
INGRESS_API = "{}/transcribe".format(INGRESS_HOST)
JOB_API = "{}/job/".format(INGRESS_HOST)
FILE = "bonjour.wav" #"small_conv_2.wav"
FORMAT= "raw"
NO_CACHE=True

if __name__ == "__main__":
    try:
        response = requests.post(INGRESS_API, headers={"accept":"application/json"}, data={"format" : FORMAT, "no_cache": NO_CACHE}, files={'file' : open(FILE, 'rb').read()})
    except:
        print("Failed to establish connexion at {}".format(INGRESS_API))
        exit(-1)
    if response.status_code not in [200, 201]:
        print("Failed to join API at {} ({})".format(INGRESS_API, response.status_code))
        exit(-1)

    content = json.loads(response.text)
    # If response if already available (200)
    if response.status_code == 200:
        print("Response cached:")
        print(content)
        exit(1)
    
    task_id = content["jobid"]
    print(response)
    print("Task ID: {}".format(task_id))
    while True:
        response = requests.get(JOB_API + task_id, headers={"accept":"application/json"})
        if response.status_code not in [200, 201, 202]:
            print("\nReturn code: {}".format(response.status_code))
            print(response.text)
            exit(-1)
        content = json.loads(response.text)
        state = content["state"]
        try:
            if state == "started":
                progress = content["progress"]
                print("Task in progress {}/{} ({})".format(progress["current"], progress["total"], progress["step"]), end="\r")
            elif state == "pending":
                print("Task is pending ...", end="\r")
            elif state == "done":
                result = content["result"]
                break
            elif state == "failed":
                print("Task failed : {}".format(content["reason"]))
                exit(1)
            else:
                print("\nOther state: {}".format(state))
                exit(-1)
            time.sleep(1)
        except Exception as e:
            print(e)
            print(content)
        time.sleep(1)
    
    print("\nFinal Result:")
    print(result)