# WIP

## Environement Variables Configuration

| Env variable| Description | Example |
|:-|:-|:-|
|SERVICE_NAME| STT service name, use to connect to the proper redis channel and mongo collection|my_stt_service|
|RESSOURCE_FOLDER|Audio Saving folder|~/linto_shared_mount/|
|KEEP_AUDIO|Either audio files are kept after request|1 (true) / 0 (false)|
|GUNICORN_WORKERS|Gunicorn serving worker (default 4)|4|
|REDIS_BROKER|Redis broker address|redis://redis_address:6379|
|MONGO_HOST|MongoDB results url|192.168.0.1|
|MONGO_PORT|MongoDB results port|27017|
|MONGO_USER|MongoDB user|user|
|MONGO_PSWD|MongoDB pswd|pswd|