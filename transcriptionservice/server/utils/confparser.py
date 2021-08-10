import os
import argparse

__all__ = ["createParser"]

def createParser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()

    # SHARED FOLDER
    parser.add_argument(
        '--ressource_folder',
        type=str,
        help='Shared folder root to register ressources (default=/opt/audio)',
        default=os.environ.get("RESSOURCE_FOLDER", "/opt/audio"))

    # GUNICORN
    parser.add_argument(
        '--gunicorn_host',
        type=str,
        help='Serving host (default=localhost)',
        default=os.environ.get("GUNICORN_HOST", "localhost"))
    
    parser.add_argument(
        '--gunicorn_port',
        type=int,
        help='Serving port (default=8000)',
        default=os.environ.get("GUNICORN_PORT", 8000))

    parser.add_argument(
        '--gunicorn_workers',
        type=int,
        help='Serving workers (default=4)',
        default=os.environ.get("GUNICORN_WORKERS", 4))

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