from typing import List
import time
from transcriptionservice.server.workers.utils import TranscriptionResult, SpeechSegment

clean_dict = {
    ord('.') : None,
    ord(',') : None,
    ord(':') : None,
    ord(';') : None,
    ord('!') : None,
    ord('?') : None,
}

end_chars = ['.', '?', '!', ';']

class SubtitleItem:
    """ SubTitleItem format a speech segment to subtitling item"""
    def __init__(self, segment: SpeechSegment):
        self.segment = segment

    def extendItems(self) -> List[SubtitleItem]:
        pass

    def toSRT(self, index: int,
                    max_char_line: int = 40,
                    max_lines: int = -1,
                    display_spk: bool = False) -> str:
        output = "{}\n{} --> {}\n".format(index, 
                            self.timeStampSRT(self.start),
                            self.timeStampSRT(self.stop))
        
        if display_spk:
            output += "{}: ".format(self.segment.speaker_id)

        for line in self.splitStr():
            output += "{}\n".format(line)
        return output + "\n"

    def toVTT(self) -> str:
        output = "{} --> {}\n".format(self.timeStampVTT(self.start),
                                      self.timeStampVTT(self.stop))
        
        output += "<v {}>{}\n\n".format(self.speaker, self.text)
        return output

    def splitStr(self, char_line: int = 40):
        """ Limit the number of character on a line. Split when needed"""
        output = []
        words = self.segment.split(" ")
        current_line = ""
        for word in words:
            if len(current_line) + len(word) > char_line:
                output.append(current_line.strip())
                current_line = ""
            current_line += "{} ".format(word)
        output.append(current_line.strip())

        return output

    def timeStampSRT(self, t_str) -> str:
        """ Format second string format to hh:mm:ss,ms SRT format """
        t = float(t_str)
        ms = t % 1
        timeStamp = time.strftime('%H:%M:%S,', time.gmtime(t))
        return "{}{:03d}".format(timeStamp, int(ms*1000))

    def timeStampVTT(self, t_str) -> str:
        """ Format second string format to hh:mm:ss,ms SRT format """
        t = float(t_str)
        ms = t % 1
        t = int(t)
        s = t % 60
        t -= s
        m = t // 60
        return "{:02d}:{:02d}.{:03d}".format(m, s, int(ms*1000))

class Subtitles:
    def __init__(self, transcription: TranscriptionResult):
        self.transcription = transcription
        self._setupItems()
        self.subtitleItems = []

    def _setupItems(self):
        for segment in self.transcription.segments:
            item = SubtitleItem(segment)
            self.subtitleItems.extend(item.extendItems())

    def segmentToSubtitleItems(self, segment: SpeechSegment, next_item_skip: float = 2.0) -> List[SubtitleItem]:
        items = []
        current_words = []
        if segment.processed_segment is None:
            pass # Considered as an unique item
        processed_words = processed_segment.split(" ")
        for i, word in segment.words:
            current_words.append(processed_words[i])
            if processed_words[i][-1] in [".", ";", "!", "?", ":"]:
                item.append(SubtitleItem(#quoi envoyer ? TimeStamps word and processed))
                current_words = []
            

            
            
    
    def toSRT(self, subtitleConf: dict) -> str:
        pass 

    def toVTT(self, subtitleConf: conf) -> str:
        pass