import os
from typing import List, Tuple, Union

from transcriptionservice.server.formating.subtitling import Subtitles
from transcriptionservice.transcription.transcription_result import \
    TranscriptionResult

from .normalization import cleanText, textToNum, removeWordPunctuations


def formatResult(
    result: dict,
    return_format: str,
    raw_return: bool = False,
    convert_numbers: bool = False,
    user_sub: List[Tuple[str, str]] = [],
    remove_punctuation_from_words: bool = True,
    remove_empty_words: bool = True,
    ensure_no_spaces_in_words: bool = True,
) -> Union[dict, str]:
    """Format result using result query parameters

    Keyword arguments:

    - result (dict): The result as stored in the result database
    - return_format (str) : Return format [application/json | text/plain | text/vtt | text/srt]
    - raw_return (bool) : If True, returns the raw transcription result
    - convert_numbers (bool): If True, converts the numbers to digits
    - user_sub (List[Tuple[str, str]]): A list of tuple for custom substitution in the final transcription.

    """

    language = os.environ.get("LANGUAGE", "")
    # Get the detected language if any
    if (not language or language == "*") and result.get("segments"):
        detected_language = result["segments"][0].get("language")
        if detected_language and detected_language != "*" and not language.startswith(detected_language):
            language = detected_language

        # If STT is capable of language detection, it is probably Whisper STT, which also returns numbers...
        # This is a ugly hack to avoid converting numbers to digits for Whisper STT (Tom said it was complicated to send convert_numbers=False...)
        convert_numbers = False

    if convert_numbers:
        fulltext_cleaner = lambda text: textToNum(cleanText(text, language, user_sub), language)
    else:
        fulltext_cleaner = lambda text: cleanText(text, language, user_sub)

    if return_format == "application/json":
        for seg in result["segments"]:
            seg["segment"] = fulltext_cleaner(seg["segment"])
            if remove_punctuation_from_words:
                for word in seg["words"]:
                    word["word"] = removeWordPunctuations(word["word"], ensure_no_spaces_in_words=ensure_no_spaces_in_words)
            elif ensure_no_spaces_in_words:
                for word in seg["words"]:
                    assert " " not in word["word"], f"Got unexpected word containing space: {word['word']}"
            if remove_empty_words:
                seg["words"] = [word for word in seg["words"] if word["word"]]
        result["transcription_result"] = fulltext_cleaner(result["transcription_result"])
        return result

    elif return_format == "text/plain":
        final_result = fulltext_cleaner(
            result["transcription_result" if not raw_return else "raw_transcription"]
        )
        return final_result

    elif return_format == "text/vtt":
        t_result = TranscriptionResult.fromDict(result)
        return Subtitles(t_result, language).toVTT(
            return_raw=raw_return, text_cleaner=fulltext_cleaner, user_sub=user_sub
        )

    elif return_format == "text/srt":
        t_result = TranscriptionResult.fromDict(result)
        return Subtitles(t_result, language).toSRT(
            return_raw=raw_return, text_cleaner=fulltext_cleaner, user_sub=user_sub
        )

    else:
        raise Exception("Unknown return format")

