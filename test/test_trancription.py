#!/usr/bin/env python3
import argparse
import os
import requests
import json
import time

def main(args):
    INGRESS_API = "{}/transcribe".format(args.transcription_server)
    JOB_API = "{}/job/".format(args.transcription_server)
    start_time = time.time()
    transcription_config = {
        "enableDiarization": args.diarization,
        "enablePunctuation": args.punctuation,
        "diarizationSpeakerCount": args.speakers, 
    }

    return_format = "application/json" if args.format == "json" else "text/plain"

    try:
        response = requests.post(INGRESS_API, 
                                 headers={"accept":return_format},
                                 data={"config" : json.dumps(transcription_config),
                                       "force_sync": args.force_sync,
                                       "no_cache" : args.no_cache},
                                 files={os.path.basename(args.audio_file) : open(args.audio_file, 'rb').read()})
    except Exception as e:
        print(str(e))
        print("Failed to establish connexion at {}".format(INGRESS_API))
        exit(-1)
    if response.status_code not in [200, 201]:
        print("Failed to join API at {} ({})".format(INGRESS_API, response.status_code))
        exit(-1)

    
    # If response if already available (200)
    if response.status_code == 200:
        print("Response cached:")
        try:
            result = json.loads(response.text)
        except:
            result = response.text
        print(result)
        exit(1)
    
    task_id = json.loads(response.text)["jobid"] if return_format == "application/json" else response.text 
    print(response)
    print("Task ID: {}".format(task_id))
    while True:
        response = requests.get(JOB_API + task_id, headers={"accept":return_format})
        if response.status_code in [200, 400]:
            print("\nReturn code: {}".format(response.status_code))
            break
        try:
            content = json.loads(response.text)
        except Exception:
            print("\n" + response.text)
            exit(-1)
        state = content["state"]
        try:
            if state == "started":
                progress = content["progress"]
                print("Task in progress {}/{} ({})\t\t\t".format(progress["current"], progress["total"], progress["step"]), end="\r")
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
    
    print("Process time = {:.2f}s".format(time.time() - start_time))
    if args.to_file is not None:
        try:
            with open(args.to_file, "w") as f:
                f.write(response.text)
        except Exception as e:
            print("Failed to write {}: {}".format(args.to_file, str(e)))
    print("\nFinal Result:")
    print(type(response.text))
    try:
        result = json.loads(response.text)["transcription_result"]
    except Exception as e:
        result = response.text
    print(result)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Feature Test')
    parser.add_argument('transcription_server', help="Transcription service API", type=str)
    parser.add_argument('audio_file', help="File to transcript", type=str)
    parser.add_argument('--format', help="Outputformat: raw|json", type=str, default="raw")
    parser.add_argument('--diarization', help="Do speaker diarization", action="store_true")
    parser.add_argument('--punctuation', help="Do punctuation", action="store_true")
    parser.add_argument('--speakers', help="Number of speakers", type=int, default=None)
    parser.add_argument('--no_cache', help="Do not use cached result", action="store_true")
    parser.add_argument('--force_sync', help="Force synchronous request", action="store_true")
    parser.add_argument('--to_file', help="Write result in a file", default=None)
    args = parser.parse_args()
    main(args)