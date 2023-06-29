import logging
import re

from text_to_num import alpha2digit

basic_sub = [("' ", "'"), ("\?", " ?"), ("!", " !"), (r"\s+", " ")]

lang_spec_sub = {
    "fr": [
        (r"\bpour cent\b", "%"),
        (r"\bpourcent\b", "%"),
        (r"(^|[^\dA-Z])([1])([^\d:]|$)", r"\1un\3"), # WTF?
    ]
}

logger = logging.getLogger("__transcription-service__")


def textToNum(text: str, language: str) -> str:
    return "\n".join([alpha2digit(elem, language[:2]) for elem in text.split("\n")])


def cleanText(text: str, language: str, user_sub: list) -> str:

    # Basic substitutions
    for elem, target in basic_sub:
        text = re.sub(elem, target, text)

    # Language specific substitutions
    for elem, target in lang_spec_sub.get(language[:2], []):
        text = re.sub(elem, target, text)

    # Request specific substitions
    for elem, target in user_sub:
        text = re.sub(elem, target, text)

    return text


# All symbols and punctuations except apostrophe ('), hyphen (-) and underscore (_)
# and the space character (which can separate several series of punctuation marks)
# Example of punctuations that can output models like Whisper: !,.:;?¿،؛؟…、。！，：？>/]:!(~\u200b[ா「«»“”"< ?;…,*」.)'
_punctuation_regex = r"[^\w\'\-_]"
_leading_punctuations_regex = r"^" + _punctuation_regex + r"+"
_trailing_punctuations_regex = _punctuation_regex + r"+$"


def removeWordPunctuations(text: str, ensure_no_spaces_in_words: bool=True) -> str:
    text = text.strip()
    # Note: we don't remove dots inside words (e.g. "ab@gmail.com")
    new_text = re.sub(_leading_punctuations_regex, "", text) #.lstrip()
    new_text = re.sub(_trailing_punctuations_regex, "", new_text) #.rstrip()
    # Let punctuation marks that are alone
    if not new_text:
        new_text = text
    # Ensure that there is no space in the middle of a word
    if ensure_no_spaces_in_words and " " in new_text:
        logger.warning(f"Got unexpected word containing space: {new_text}")
        new_text, tail = new_text.split(" ", 1)
        # OK if the tail only contains non alphanumeric characters (then we just keep the first part)
        assert not re.search(r"[^\W\d\'\-_]", tail), f"Got unexpected word containing space: {text}"
        return removeWordPunctuations(new_text, ensure_no_spaces_in_words=ensure_no_spaces_in_words)
    return new_text
