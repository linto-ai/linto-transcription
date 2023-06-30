import unittest

# Set PYTHONPATH
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

# Import what to test
from transcriptionservice.server.formating.normalization import (
    cleanText,
    removeWordPunctuations,
)


class TestFormating(unittest.TestCase):

    def test_format_word(self):

        # all kinds of punctuations
        puncs = "!,.:;?¿،؛؟…、。！，：？>/]:!(~\u200b[ா「«»“”\"<?;…...:,*」.)[]\{\}"

        # Test things that should be left unchanged
        for word in [
            # Simple cases
            "hello",
            "123",
            # Leave apostrophe/hyphen/underscore
            "l'", "'allo",
            "peut-être-", "-peut-être", " -", "- ", " - ",
            "hello_", "_hello", "_hello_",
            # Leave punctuations inside words
            "me@mail.com", 
            "http://www.website.com",
            "a"+puncs+"b",
            "'"+puncs+"'", "-"+puncs+"-", "_"+puncs+"_",
            # Leave isolated punctuations
            ".", puncs,
            ]:

            self.assertEqual(
                removeWordPunctuations(word),
                word.strip()
            )

        # Test things that should be changed
        for input, expected in [
            # Simple cases
            ("bon.", "bon"),
            ("Hello!", "Hello"),
            ("peut-être ?", "peut-être"),
            ("2004,", "2004"),
            ("http://www.website.com/", "http://www.website.com"),
            # Repeated punctuations
            ("tiens...", "tiens"),
            ("tiens!!!", "tiens"),
            ("...tiens…", "tiens"),
            ("“2004,”", "2004"),
            # Replace punctuations with spaces
            ("2004, «", "2004"),
            (puncs + " " + puncs + "hello" + puncs + " " + puncs, "hello"),
            (puncs + " " + puncs + " hello " + puncs + " " + puncs, "hello"),
            (puncs + " " + puncs + "'hello'" + puncs + " " + puncs, "'hello'"),
            (puncs + " " + puncs + " _'hello'_ " + puncs + " " + puncs, "_'hello'_"),
            # Corner case
            ("hello '", "hello"),
        ]:
            self.assertEqual(
                removeWordPunctuations(input),
                expected
            )

        # Test things that should raised exceptions
        for input in [
            # Several words
            "hello world",
            # Corner cases
            "' hello '",
            "' hello",
        ]:
            self.assertRaises(AssertionError,
                removeWordPunctuations,
                input,
            )

    def test_clean_text(self):

        LANG = "fr-FR"

        expected = 'Oui ? Oui ! Oui, oui. « oui ».'
        for input in [
            'Oui? Oui! Oui, oui.«oui».',
            'Oui ? Oui ! Oui , oui . « oui » .',
            "Oui  ?  Oui  !  Oui  ,  oui  .  «  oui  »  .",
        ]:
            self.assertEqual(
                cleanText(input, LANG, []),
                expected
            )

        LANG = "en-US"
        expected = 'Oui? Oui! Oui, oui. « oui ».'
        for input in [
            'Oui? Oui! Oui, oui.«oui».',
            'Oui ? Oui ! Oui , oui . « oui » .',
            "Oui  ?  Oui  !  Oui  ,  oui  .  «  oui  »  .",
        ]:
            self.assertEqual(
                cleanText(input, LANG, []),
                expected
            )


if __name__ == '__main__':
    unittest.main()
