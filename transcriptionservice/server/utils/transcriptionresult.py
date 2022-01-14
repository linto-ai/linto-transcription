from dataclasses import dataclass, field
from typing import Union, List, Tuple, Dict
import json

from .transcriptionconfig import TranscriptionConfig

@dataclass
class Word:
    word: str
    start: float 
    end: float
    conf: float
    
    def apply_offset(self, offset: float):
        self.start += offset
        self.end += offset

    @property
    def json(self) -> dict:
        return self.__dict__

@dataclass
class SpeechSegment:
    speaker_id: str = None
    words: list = field(default_factory=list)

    def toString(self, include_spkid: bool = False, spk_sep: str = ":"):
        output = f"{self.speaker_id}{spk_sep} " if include_spkid else ""
        sentence = " ".join([w.word for w in self.words])
        return output + sentence
    
    @property
    def start(self) -> float:
        return min([w.start for w in self.words])

    @property
    def end(self) -> float:
        return max([w.end for w in self.words])

    @property
    def duration(self) -> float:
        return self.end - self.start

    @property
    def json(self) -> dict:
        return {
            "spk_id": self.speaker_id,
            "start": self.start,
            "end": self.end,
            "duration": self.duration,
            "sentence": self.toString(),
            "words": [w.json for w in self.words]
        }

class TranscriptionResult:
    """ Transcription result manages transcription results, post-processing and formating for transcription results."""
    transcription_confidence = 0.0
    raw_transcription = ""
    words = []
    diarization_data = {}
    segments = []
    punctuated = []

    def __init__(self, transcriptions: List[Tuple[dict, float]], config: TranscriptionConfig):
        """ Initialisation accepts list of tuple (transcription, time_offset) """
        self.config = config
        self._mergeTranscription(transcriptions)

    def _mergeTranscription(self, transcriptions: List[Tuple[str, float]]):
        """ Merges transcription results applying offsets """
        for transcription, offset in transcriptions:
            self.raw_transcription += transcription["text"] + " "
            for w in transcription["words"]:
                word = Word(**w)
                word.apply_offset(offset)
                self.words.append(word)
            self.transcription_confidence += transcription["confidence-score"]
        self.transcription_confidence /= len(transcriptions)
        self.words.sort(key=lambda x: x.start)
        

    def setDiarizationResult(self, diarizationResult: Union[str, dict]):
        self.diarization_data = json.loads(diarizationResult) if isinstance(diarizationResult, str) else diarizationResult
        self.words.sort(key=lambda x: x.start)

        segments = sorted(self.diarization_data["segments"], key=lambda x: x["seg_begin"])
        
        spk_index = 0
        current_id = segments[spk_index]["spk_id"]
        current_words = []
        
        for word in self.words:
            if word.start > segments[spk_index]["seg_end"]: # Next segment
                if len(current_words):
                    self.segments.append(SpeechSegment(current_id, current_words))
                if spk_index + 1 < len(segments):
                    spk_index += 1
                current_id = segments[spk_index]["spk_id"]
                current_words = []
            current_words.append(word)
        if len(current_words):
            self.segments.append(SpeechSegment(current_id, current_words))

    @property
    def raw_text(self) -> str:
        if (self.segments):
            return "\n".join([seg.toString(include_spkid=True) for seg in self.segments])
        else:
            return self.raw_transcription

    def final_result(self) -> dict:
        result = dict()
        result["raw_transcription"] = self.raw_transcription
        result["transcription_result"] = self.raw_text
        result["segments"] = []
        if self.config.diarizationConfig["enableDiarization"]:
            print(self.segments)
            result["segments"] = [s.json for s in self.segments]
        return result