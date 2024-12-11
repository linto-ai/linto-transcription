import logging
import regex as re # for using things like \p{Sc} (currencies)

from text_to_num import alpha2digit

lang_spec_sub = {
    "fr": [
        # Add spaces around «»
        (r"([" + re.escape('«»') + r"])", r" \1 "),
        # Add a space before double punctuation marks
        (r"([" + re.escape('?!:;') + r"])", r" \1"),
        # Remove space before simple punctuation marks
        (r"\s+([" + re.escape(',.') + r"])", r"\1"),
    ],
}

default_sub = [
    # Add spaces around «»
    (r"([" + re.escape('«»') + r"])", r" \1 "),
    # Remove space before punctuation marks
    (r"\s+([" + re.escape('?!:;,.') + r"])", r"\1"),
]

logger = logging.getLogger("__transcription-service__")


def textToNum(text: str, language: str) -> str:
    if language == "*":
        logger.warning("Language not specified, not converting numbers to digits")
        return text
    if len(language) < 2:
        raise ValueError(f"Invalid language code '{language}'")
    lang = language[:2].lower()
    # Note: we could add symbols conversions as well (e.g. "euros" -> "€", "pour cent" -> "%", etc.)
    #       but this seems awkward and prone to downstream bugs
    return "\n".join([_alpha2digit(elem, lang) for elem in text.split("\n")])

def _alpha2digit(text: str, language: str) -> str:
    try:
        return alpha2digit(text, language)
    except Exception as err:
        text_small = text
        if len(text) > 200:
            text_small = text[:100] + "..." + text[-100:]
        logger.warning(f"Error converting '{text_small}' to digits with {language=} ({err})")
        return text

def cleanText(text: str, language: str, user_sub: list) -> str:

    # Language specific substitutions
    for elem, target in lang_spec_sub.get(language[:2], default_sub):
        text = re.sub(elem, target, text)

    # Request specific substitions
    for elem, target in user_sub:
        text = re.sub(elem, target, text)

    # Remove duplicated spaces
    text = re.sub(r"\s+", " ", text)

    return text


# All punctuations and symbols EXCEPT:
# * apostrophe (') and hyphen (-)
# * underscore (_)
# * currency symbols ($, €, £, ...) -> \p{Sc}
# * math symbols (%, +, ×). ex: C++
# * misc (#, @). ex: C#, @user
# and the space character (which can separate several series of punctuation marks)
# Example of punctuations that can output models like Whisper: !,.:;?¿،؛؟…、。！，：？>/]:!(~\u200b[ா「«»“”"< ?;…,*」.)'
_punctuation_regex = r"[^\w\p{Sc}" + re.escape("'-_%+×#@&²³½") + "]"
_leading_punctuations_regex = r"^" + _punctuation_regex + r"+"
_trailing_punctuations_regex = _punctuation_regex + r"+$"

# A list of symbols that can be an isolated words and not in the exclusion list above
# * &
# * candidates not retained: §, <, =, >, ≤, ≥
_maybe_word_regex = None # r"[" + re.escape("&") + r"]$"


def removeWordPunctuations(text: str, ensure_no_spaces_in_words: bool=True) -> str:
    text = text.strip()
    # Note: we don't remove dots inside words (e.g. "ab@gmail.com")
    new_text = re.sub(_leading_punctuations_regex, "", text) #.lstrip()
    new_text = re.sub(_trailing_punctuations_regex, "", new_text) #.rstrip()
    # Let punctuation marks that are alone
    if not new_text:
        if _maybe_word_regex and re.match(_maybe_word_regex, text):
            new_text = text
        else:
            new_text = ""
    # Ensure that there is no space in the middle of a word
    if ensure_no_spaces_in_words and " " in new_text:
        logger.warning(f"Got unexpected word containing space: {new_text}")
        first, second = new_text.split(" ", 1)
        first_is_word = bool(re.search(r"[^\W\'\-_]", first))
        second_is_word = bool(re.search(r"[^\W\'\-_]", second))
        if first_is_word and second_is_word:
            raise RuntimeError(f"Got unexpected word containing space: '{new_text}'")
        new_text = first if first_is_word else second
        return removeWordPunctuations(new_text, ensure_no_spaces_in_words=ensure_no_spaces_in_words)
    return new_text
