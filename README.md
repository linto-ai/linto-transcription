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
* One or multiple instances of [linto-standalone-worker](https://github.com/linto-ai/linto-platform-stt-standalone-worker) > 3.2.0 running and configured with the same `SERVICE_NAME`.
* A message broker (like redis) running at `SERVICES_BROKER`.
* A mongo DB running at `MONGO_HOST:MONGO_PORT`.

Optionnaly, for specific transcription format the following are needed:
* One or multiple instances of [linto-diarization-worker](https://github.com/linto-ai/linto-platform-speaker-diarization-worker) > 1.1.0 for speaker diarization configured on the same service broker.
* One or multiple instances of [linto-punctuation-worker](https://github.com/linto-ai/linto-platform-text-punctuation-worker) > 1.1.0 for text punctuation configured on the same service broker.

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
docker run --rm -it -p $SERVING_PORT:80 -p $FLOWER_SERVING_PORT:5555 \
    -v $YOUR_SHARED_FOLDER:/opt/audio \
    --env-file .env \
    --name service-manager \
    transcription_service \
    /bin/bash
```
Fill ```SERVING_PORT```, ```FLOWER_SERVING_PORT```, ```YOUR_SHARED_FOLDER``` with your values.

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
|RESSOURCE_FOLDER|Shared folder (host)|~/linto_shared_mount/|
|KEEP_AUDIO|Either audio files are kept after request|1 (true) / 0 (false)|
|GUNICORN_WORKERS|Gunicorn serving worker (default 4)|4|
|SERVICES_BROKER|Redis broker address|redis://broker_address:6379|
|MONGO_HOST|MongoDB results url|my-mongo-service|
|MONGO_PORT|MongoDB results port|27017|
|MONGO_USER|MongoDB user|user|
|MONGO_PSWD|MongoDB pswd|pswd|

## API
The transcription service offers a transcription API REST to submit transcription requests.

### /api-doc
The /api-doc route offers a swagger interface with the available routes and their parameters.
You can use it to localy test the different routes.

### /transcribe
The /transcribe route allows POST request containing an audio file.

|Parameter| Description | Required |
|:-|:-|:-|
|format|Return's format [raw/speakers/formated]|**True**|
|spk_number|Number of speakers|Required for [speakers/formated] formats|
|no_cache|If set to true, doesn't fetch result from database|**False**|

If the request is accepted, answer will be ```201``` with a json response containing the jobid.
```json
{"jobid" : "the-job-id"""}
```

If the result has already been computed, the request returns a ```200``` with the transcription.

#### Return formats
There are 3 transcriptions formats:

**raw**: Returns a raw text transcription of the audio.

**speakers**: Return an json object containing:
```json
{
    "confidence-score": -4.6663191855070194e+21, #Utterance confidence score
    "speakers": [ # An array of speakers
        {
            "speaker_id": "spk1", # Speaker id
            "words": [ #Words
                {
                    "conf": 1.0, # Word confidence score 
                    "end": 0.78, # Word end timestamp
                    "start": 0.0, # Word start timestamp
                    "word": "bonjour" # Word
                }
            ]
        }
    ], 
    "text": ["spk1: bonjour"] # Turns of speech with speaker id 
}
```
 
**formated**: Returns an array with the turn of speech and speakers identification
```json
["spk1: bonjour"]
```

> ```speakers``` and ```formated``` formats require a running speaker-diarization service

### /job/{jobid}

The /job/{jobid} GET route allow you to get the state or the result of the given job.
* If the job is **started**, it returns a code ```202``` with informations on the progress.
* If the job is **finished**, it returns a code ```200``` with the job result.
* If the jobid is **unknown or the task failed** returns a code ```400```.

## Usage
Request exemple:

```bash
cd test/

curl -X POST "http://my-transcription-service:my-serving-port/transcribe" -H "accept: application/json"\
 -H "Content-Type: multipart/form-data" \
 -F 'format=raw' \
 -F "file=@bonjour.wav;type=audio/wav"
```