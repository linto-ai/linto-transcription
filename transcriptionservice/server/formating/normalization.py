import logging
import re

from text_to_num import alpha2digit

basic_sub = [("' ", "'"), ("\?", " ?"), ("!", " !"), (" +", " ")]

lang_spec_sub = {
    "fr_FR": [
        ("pour cent", "%"),
        ("pourcent", "%"),
        (r"(^|[^\dA-Z])([1])([^\d:]|$)", r"\1un\3"),
    ]
}

logger = logging.getLogger("__services_manager__")


def textToNum(text: str, language: str) -> str:
    return "\n".join([alpha2digit(elem, language[:2]) for elem in text.split("\n")])


def cleanText(text: str, language: str, user_sub: list) -> str:
    clean_text = text

    # Basic substitutions
    for elem, target in basic_sub:
        text = re.sub(elem, target, text)

    # Language specific substitutions
    for elem, target in lang_spec_sub.get(language, []):
        text = re.sub(elem, target, text)

    # Request specific substitions
    for elem, target in user_sub:
        text = re.sub(elem, target, text)

    return text

# string.punctuation, plus Whisper specific "«»¿", minus apostrophe "'" and dash "-"
_punctuations = '.!"#$%&()*+,/:;<=>?@[\\]^_`{|}~«»¿' + "。，！？：”、…" + '؟،؛' + '—'
_punctuations_regex = "["+re.escape(_punctuations)+"]"

def removeFinalPunctuations(text: str) -> str:
    text = text.strip()
    # We don't remove dots inside words (e.g. "ab@gmail.com")
    new_text = re.sub(rf"{_punctuations_regex}$", "", text).strip()
    # Let punctuation marks that are alone
    if not new_text and " " not in text:
        new_text = text
    return new_text
