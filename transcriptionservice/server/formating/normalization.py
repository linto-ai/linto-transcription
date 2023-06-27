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

# string.punctuation, plus Whisper specific "«»¿", plus Arabic/Russian, minus apostrophe "'" and dash "-"
_punctuations = '.!"#$%&()*+,/:;<=>?@[\\]^_`{|}~«»¿。，！？：”、…؟،؛—'
# special characters that can occur along with ?!;: in Whisper tokens
_punctuations += '்\u200bா「 」'
assert " " in _punctuations
_trailing_punctuations_regex = r"["+re.escape(_punctuations)+"]+$"

def removeTrailingPunctuations(text: str, ensure_no_spaces_in_words: bool=True) -> str:
    text = text.strip()
    # Note: we don't remove dots inside words (e.g. "ab@gmail.com")
    new_text = re.sub(_trailing_punctuations_regex, "", text)
    # Let punctuation marks that are alone
    if not new_text:
        new_text = text
    # Ensure that there is no space in the middle of a word
    if ensure_no_spaces_in_words and " " in new_text:
        logger.warning(f"Got unexpected word containing space: {new_text}")
        new_text, tail = new_text.split(" ", 1)
        # OK if the tail only contains non alphanumeric characters (then we just keep the first part)
        assert not re.search(r"[^\W\d_]", tail), f"Got unexpected word containing space: {text}"
    return new_text
