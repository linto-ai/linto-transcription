from text_to_num import alpha2digit
import re

basic_sub = [("' ", "'"),
             ("?", " ?"),
             ("!", " !"),
            (" +" ," ")]

lang_spec_sub = {
    "fr_FR": [("pour cent", "%"), 
              ("pourcent", "%"), 
              ]
}

def textToNum(text: str, language: str) -> str:
    return "\n".join([alpha2digit(elem, language[:2]) for elem in text.split("\n")])

def cleanText(text: str, language: str, user_sub: list) -> str:
    clean_text = text
    sub_list = [("' ", "'"),
                (" +" ," ")]

    # Basic substitutions
    for elem, target in sub_list:
        text = re.sub(elem, target, text)
    
    # Language specific substitutions
    for elem, target in lang_spec_sub.get(language, []):
        text = re.sub(elem, target, text)
    
    # Request specific substitions
    for elem, target in user_sub:
        text = re.sub(elem, target, text)

    return text
