import os
import argparse

__all__ = ["createParser"]

def createParser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()


    # GUNICORN
    parser.add_argument(
        '--gunicorn_workers',
        type=int,
        help='Serving workers (default=4)',
        default=os.environ.get("GUNICORN_WORKERS", 4))

    # SWAGGER
    parser.add_argument(
        '--swagger_url',
        type=str,
        help='Swagger interface url',
        default='/api-doc')
    parser.add_argument(
        '--swagger_prefix',
        type=str,
        help='Swagger prefix',
        default=os.environ.get('SWAGGER_PREFIX', ''))
    parser.add_argument(
        '--swagger_path',
        type=str,
        help='Swagger file path',
        default=os.environ.get('SWAGGER_PATH', '/usr/src/app/transcriptionservice/document/swagger.yaml'))

    # MONGODB
    parser.add_argument(
        '--mongo_uri',
        type=str,
        help='MongoDB host',
        default=os.environ.get("MONGO_HOST", None))

    parser.add_argument(
        '--mongo_port',
        type=int,
        help='MongoDB port',
        default=os.environ.get("MONGO_PORT", None))
    
    # TRANSCRIPTION
    parser.add_argument(
        '--service_name',
        type=str,
        help='Service name (default=stt)',
        default=os.environ.get("SERVICE_NAME", "stt"))

    # MISC
    parser.add_argument(
        '--keep_audio',
        action='store_true',
        help='If true audio-files are kept after the request end')

    parser.add_argument(
        '--debug',
        action='store_true',
        help='Display debug logs')

    return parser