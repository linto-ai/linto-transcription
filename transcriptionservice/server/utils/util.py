import hashlib
import os
import subprocess
from typing import Dict, List

from transcriptionservice.transcription.configs.transcriptionconfig import \
    TranscriptionConfig

__all__ = ["fileHash", "requestlog", "read_timestamps"]


def fileHash(f):
    """Returns md5 hash hexdigest"""
    return hashlib.md5(f).hexdigest()


def requestlog(logger, origin: str, config: TranscriptionConfig, hashed: str, result_cached: bool):
    """Displays request parameters as log INFO"""
    logger.info(
        """Request received:\n
                Origin: {}\n 
                Hash: {}\n
                Param: {}\n
                Result_cached: {}""".format(
            origin, hashed, str(config), result_cached
        )
    )


def read_timestamps(file_buffer: bytes) -> List[Dict]:
    """Read the timestamps file attached to a transcription request

    Args:
        file_buffer (bytes): Utf-8 encoded text file buffer. Expected format is lines containing 1.123 2.54 [1] : start stop [id]

    Raises:
        ValueError: Failed to read timestamp file

    Returns:
        List[Dict]: List of timestamps object e.g. [{"start": 1.123, "end": 2.54, "id": 1},]
    """
    lines = file_buffer.decode("utf8").split("\n")
    timestamps = []
    for i, line in enumerate(lines):
        if not line.strip():
            continue
        try:
            if len(line.split(" ")) == 3:
                s, e, id = line.split(" ")
            else:
                s, e = line.split(" ")
                id = None
            timestamps.append({"start": float(s), "end": float(e), "spk_id": id})
        except Exception as ex:
            raise ValueError(f"Failed to read timestamps at line {i} - {line}: {str(ex)}")
    return timestamps
