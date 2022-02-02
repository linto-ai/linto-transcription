import os
from typing import Union, List, Tuple

from transcriptionservice.workers.utils import TranscriptionResult
from transcriptionservice.server.utils.subtitling import Subtitles
from .normalization import textToNum, cleanText

def formatResult(result: dict, 
                 return_format: str, 
                 raw_return: bool = False, 
                 convert_numbers: bool = False, 
                 user_sub: List[Tuple[str, str]] = []) -> Union[dict, str]:
    """ Format result using result query parameters 
    
    Keyword arguments:

    - result (dict): The result as stored in the result database
    - return_format (str) : Return format [application/json | text/plain | text/vtt | text/srt]
    - raw_return (bool) : If True, returns the raw transcription result
    - convert_numbers (bool): If True, converts the numbers to digits
    - user_sub (List[Tuple[str, str]]): A list of tuple for custom substitution in the final transcription.
    
    """ 
    language = os.environ.get("LANGUAGE", "")
    if return_format == 'application/json':
        for seg in result["segments"]:
            seg["segment"] = cleanText(seg["segment"], language, user_sub)
            if convert_numbers:
                seg["segment"] = textToNum(seg["segment"], language)
        result["transcription_result"] = cleanText(result["transcription_result"], language, user_sub)
        if convert_numbers:
            result["transcription_result"] = textToNum(result["transcription_result"], language)
        return result
    elif return_format == 'text/plain':
        final_result = cleanText(result["transcription_result" if not raw_return else "raw_transcription"], language, user_sub)
        if convert_numbers:
            final_result = textToNum(final_result, language)
        return final_result
    elif return_format == 'text/vtt':
        t_result = TranscriptionResult.fromDict(result)
        return Subtitles(t_result).toVTT(language)

    elif return_format == 'text/srt':
        t_result = TranscriptionResult.fromDict(result)
        return Subtitles(t_result).toSRT()
    else:
        raise Exception("Unknown return format")
