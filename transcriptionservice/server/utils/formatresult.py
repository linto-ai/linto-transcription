import os

from typing import Union
from transcriptionservice.workers.utils import TranscriptionResult
from transcriptionservice.server.utils.subtitling import Subtitles

def formatResult(result: dict, return_format: str) -> Union[dict, str]:
    if return_format == 'application/json':
        return result
    elif return_format == 'text/plain':
        return result["transcription_result"]
    elif return_format == 'text/vtt':
        t_result = TranscriptionResult.fromDict(result)
        return Subtitles(t_result).toVTT(os.environ.get("LANGUAGE", ""))

    elif return_format == 'text/srt':
        t_result = TranscriptionResult.fromDict(result)
        return Subtitles(t_result).toSRT()
    else:
        return "Unknown format"