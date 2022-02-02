#!/usr/bin/env python3
import argparse
import os
import requests
import json
import time
HEADER_FORMAT = {"json": "application/json",
                 "text": "text/plain",
                 "vtt": "text/vtt",
                 "srt": "text/srt"}

def fetch_result(result_api: str, result_id: str, result_format: str, returnRaw: bool, convertNumbers: bool):
    response = requests.get(f"{result_api}{result_id}?convert_numbers={'true' if convertNumbers else 'false'}&return_raw={'true' if returnRaw else 'false'}",
                            headers={"accept":HEADER_FORMAT[result_format]})
    
    if response.status_code != 200:
        print(f"Failed to retrieve a result for result_id {result_id}")
        return None
    
    return response.text

def main(args):
    INGRESS_API = "{}/transcribe".format(args.transcription_server)
    JOB_API = "{}/job/".format(args.transcription_server)
    RESULT_API = "{}/results/".format(args.transcription_server)
    start_time = time.time()
    transcription_config = {
        "enablePunctuation": args.punctuation,
        "diarizationConfig": {
            "enableDiarization" : args.diarization,
            "numberOfSpeaker" : args.spknumber,
            "maxNumberOfSpeaker" :args.maxspknumber
        }
    }

    # Initial request
    try:
        response = requests.post(INGRESS_API, 
                                 headers={"accept":"application/json"},
                                 data={"transcriptionConfig" : json.dumps(transcription_config),
                                       "force_sync": False,},
                                files={os.path.basename(args.audio_file) : open(args.audio_file, 'rb').read()})
    except Exception as e:
        print(str(e))
        print("Failed to establish connexion at {}".format(INGRESS_API))
        exit(-1)

    if response.status_code != 201:
        print("Failed to join API at {} ({})".format(INGRESS_API, response.status_code))
        exit(-1)
    
    # Job ID
    task_id = json.loads(response.text)["jobid"]
    print("Task ID: {}".format(task_id))

    # Following task progress
    while True:
        response = requests.get(JOB_API + task_id, headers={"accept":"application/json"})
        if response.status_code == 201:
            result_id = json.loads(response.text)["result_id"]
            print(f"\nResult id: {result_id}")
            break
        elif response.status_code == 400:
            print("Task has failed: {}".format(response.text))
            exit(-1)
        try:
            content = json.loads(response.text)
            state = content.get("state")
        except Exception as e:
            print("\nFailed to retrieve state: {} because of {}".format(response.text, str(e)))
            exit(-1)
        
        try:
            if state == "started":
                progress = content["progress"]
                print("Task in progress" , end="\r")
            elif state == "pending":
                print("Task is pending ...", end="\r")
            else:
                print("\nOther state: {}".format(state))
                exit(-1)
            time.sleep(1)
        except Exception as e:
            print(e)
            print(content)
        time.sleep(1)

    # Get the request result
    print("Process time = {:.2f}s".format(time.time() - start_time))
    print(f"Fetching result with result_id {result_id}")

    result = fetch_result(result_api=RESULT_API, result_id=result_id, result_format=args.format, returnRaw=args.returnraw, convertNumbers=args.convertNumbers)
    
    if args.to_file is not None:
        try:
            with open(args.to_file, "w") as f:
                f.write(result)
            print(f"Result written at {args.to_file}")
        except Exception as e:
            print("Failed to write {}: {}".format(args.to_file, str(e)))
    else:
        print("\nFinal Result:")
        print(result)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Transcription request test')
    parser.add_argument('transcription_server', help="Transcription service API", type=str)
    parser.add_argument('audio_file', help="File to transcript", type=str)
    parser.add_argument('--diarization', help="Do speaker diarization", action="store_true")
    parser.add_argument('--punctuation', help="Do punctuation", action="store_true")
    parser.add_argument('--spknumber', help="Number of speakers", type=int, default=None)
    parser.add_argument('--maxspknumber', help="Number of speakers", type=int, default=None)
    parser.add_argument('--format', help="Result format [json | text | vtt | srt]", type=str, default="text")
    parser.add_argument('--returnraw', help="Return raw transcription", action="store_true")
    parser.add_argument('--convertNumbers', help="If true replace number with digits", action="store_true")
    parser.add_argument('--to_file', help="Write result in a file", default=None)
    
    args = parser.parse_args()

    if args.format not in HEADER_FORMAT.keys():
        print("Unsupported format {}, supported formats are {}".format(args.format, HEADER_FORMAT.keys()))
        exit(-1)

    main(args)