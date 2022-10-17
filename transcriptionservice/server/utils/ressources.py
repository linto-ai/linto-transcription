import logging
import os

__all__ = ["write_ressource", "release_ressource"]

logger = logging.getLogger("__transcription-service__")


def write_ressource(
    file_content: bytes, file_name: str, ressource_folder: str, extension: str
) -> str:
    """Write ressource to the ressource folder"""
    file_path = os.path.join(ressource_folder, f"{file_name}.{extension}")
    logger.debug("Write ressource {} at {}".format(file_name, file_path))
    with open(file_path, "wb") as f:
        f.write(file_content)

    return file_path


def release_ressource(file_name: str, ressource_folder: str):
    """Remove ressource"""
    file_path = os.path.join(ressource_folder, file_name)
    logger.debug("Removing ressource {} at {}".format(file_name, file_path))
    try:
        os.remove(file_path)
    except Exception as e:
        logger.warning("Failed to remvove ressource at {}: {}".format(file_path, str(e)))
