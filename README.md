# LinTO Platform Transcription service
## Description
The transcription service is the interface for requesting transcriptions.

The service allows you to:
* Request asynchronous transcriptions from audio file.
* Follow transcription task state and progress.
* Automaticaly store transcription results in a database.
* Use stored results to avoid recomputation.

The transcription service relies on a service message broker to call the different sub-services needed for a transcription request.

## Usage
### Prerequisites
To use the transcription service you must have at least:
* One or multiple instances of [linto-platform-stt](https://github.com/linto-ai/linto-platform-stt) > 3.2.0 running and configured with the same `SERVICE_NAME`.
* A message broker (like redis) running at `SERVICES_BROKER`.
* A mongo DB running at `MONGO_HOST:MONGO_PORT`.

Optionnaly, for diarization or punctuation the following are needed:
* One or multiple instances of [linto-diarization-worker](https://github.com/linto-ai/linto-platform-diarization) > 1.1.0 for speaker diarization configured on the same service broker.
* One or multiple instances of [linto-punctuation-worker](https://github.com/linto-ai/linto-platform-punctuation) > 1.1.0 for text punctuation configured on the same service broker (LANGUAGE must be the same).

To share audio files across the different services they must be configured with the same shared volume `RESSOURCE_FOLDER`.

## Deploy
### Using docker image
1- First build the image:
```bash
cd linto-platform-transcription-service &&
docker build . -t transcription_service
```
2- Create and fill the .env
```bash
cp .envdefault .env
```
Fill the .env with the value described bellow [Environement Variables Configuration](#environement-variables-configuration)

2- Launch a container:
```bash
docker run --rm -it -p $SERVING_PORT:80 \
    -v $YOUR_SHARED_FOLDER:/opt/audio \
    --env-file .env \
    --name my_transcription_api \
    transcription_service \
    /bin/bash
```
Fill ```SERVING_PORT```, ```YOUR_SHARED_FOLDER``` with your values.

### Using docker-compose
1- Create and fill the .env
```bash
cp .envdefault .env
```
Fill the .env with the value described bellow [Environement Variables Configuration](#environement-variables-configuration)

2- Compose
```bash
docker-compose up .
```

### Environement Variables Configuration

| Env variable| Description | Example |
|:-|:-|:-|
|SERVICE_NAME| STT service name, use to connect to the proper redis channel and mongo collection|my_stt_service|
|LANGUAGE| Language code as a BCP-47 code | fr_FR |
|RESSOURCE_FOLDER|Shared folder (host)|~/linto_shared_mount/|
|KEEP_AUDIO|Either audio files are kept after request|1 (true) / 0 (false)|
|CONCURRENCY|Number of workers (default 10)|10|
|SERVICES_BROKER|Message broker address|redis://broker_address:6379|
|BROKER_PASS|Broker Password| Password|
|MONGO_HOST|MongoDB results url|my-mongo-service|
|MONGO_PORT|MongoDB results port|27017|
|MONGO_USER|MongoDB user|user|
|MONGO_PSWD|MongoDB pswd|pswd|

## API
The transcription service offers a transcription API REST to submit transcription requests.

### /transcribe
The /transcribe route allows POST request containing an audio file.

The route accepts multipart/form-data requests.

Response format can be application/json, text/plain, text/vtt or text/srt specified in the accept field of the header.

|Form Parameter| Description | Required |
|:-|:-|:-|
|transcriptionConfig|(object optionnal) A transcriptionConfig Object describing transcription parameters | See [Transcription config](#transcription-config) |
|force_sync|(boolean optionnal) If True do a synchronous request | [true | **false** | null] |
|no_cache| (boolean optionnal) If set to true, doesn't fetch result from database|[true | **false** | null]|


If the request is accepted, answer will be ```201``` with a json or text response containing the jobid.

With accept: application/json
```json
{"jobid" : "the-job-id"}
```
With accept: text/plain
```
the-job-id
```

If the result has already been computed or the force_sync flag is set to true, the request returns a ```200``` with the transcription (see [Transcription Result](#transcription-result)).

#### Transcription config
The transcriptionConfig object describe the transcription parameters and flags of the request. It is structured as follows:
```json
{
  "transcribePerChannel": false, #Not implemented yet
  "enablePunctuation": false, # Applies punctuation
  "diarizationConfig": {
    "enableDiarization": false, #Enables speaker diarization
    "numberOfSpeaker": null, #If set, forces number of speaker
    "maxNumberOfSpeaker": null #If set and and numberOfSpeaker is not, limit the maximum number of speaker.
  }
}
```

### /job/{jobid}

The /job/{jobid} GET route allow you to get the state or the result of the given job.

Response format can be application/json, text/plain, text/vtt or text/srt specified in the accept field of the header.

* If the job state is **started**, it returns a code ```202``` with informations on the progress.
* If the job state is **finished**, it returns a code ```200``` with the [transcription result](#transcription-result).
* If the job state is **unknown** returns a code ```404```.
* If the job state is **failed** returns a code ```400```.

#### Transcription result
The transcription result format depends on the accept field of the job request.
* text/plain: Returns the final transcription as text. 
```
spk1: This is a transcription
spk2: Diarization and punctuation are set
```
* application/json: Returns a json object containing the transcription results and details.

```json
{
  "confidence": 0.9, # Overall transcription confidence
  "raw_transcription": "this is a transcription diarization and punctuation are set", # Raw transcription
  "segments": [ # Speech segment representing continious speech by a single speaker
    {
      "duration": 3.12991, # Segment duration
      "end": 3.12991, # Segment stop time
      "raw_segment": "this is a transcription", # Raw transcription of the speech segment
      "segment": "This is a transcription", # Processed transcription of the segment (punctuation, normalisation, ...)
      "spk_id": "spk1", # Speaker id
      "start": 0, # Segment start time
      "words": [ # Segment's word informations
        {
          "conf": 0.600024, # Word confidence
          "end": 0.23784, # Word stop time
          "start": 0, # Word start time
          "word": "this" # Word 
        }
        ...
      ]
    },
    {
      "duration": 4.59,
      "end": 7.71991,
      "raw_segment": "diarization and punctuation are set",
      "segment": "Diarization and punctuation are set",
      "spk_id": "spk2",
      "start": 3.12991,
      "words": [
        {
          "conf": 0.89654,
          "end": 4.1382,
          "start": 3.12991,
          "word": "diarization"
        }
        ...
      ]
    }
      ]
    }
  ],
  "transcription_result": "spk1: This is a transcription\nspk2: Diarization and punctuation are set" # Final transcription
}
```
### /docs
The /docs route offers access to a swagger-ui interface with the API specifications (OAS3).

It also allows to directly test requests using pre-filled modifiable parameters.

## Usage
Request exemple:

```bash
curl -X POST "http://HOST_ADDRESS:HOST_PORT/transcribe" -H  "accept: application/json" -H  "Content-Type: multipart/form-data" -F "transcriptionConfig={
  "transcribePerChannel": false,
  "enablePunctuation": true,
  "diarizationConfig": {
    "enableDiarization": true,
    "numberOfSpeaker": null,
    "maxNumberOfSpeaker": null
  },
  "subtitleConfig": {
    "enableSubtitle": false,
    "subtitleFormat": "VTT",
    "maxCharacterPerLine": 0
  }
}" -F "no_cache=false" -F "force_sync=false" -F "file=@MY_AUDIO.wav;type=audio/x-wav"
```

## License
This project is licensed under AGPLv3 license. Please refer to the LICENSE file for full description of the license.
