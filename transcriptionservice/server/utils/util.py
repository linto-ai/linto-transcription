import hashlib
import os
import subprocess

from transcriptionservice.transcription.configs.transcriptionconfig import TranscriptionConfig


__all__ = ["fileHash", "requestlog"]


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
