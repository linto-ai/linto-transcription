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
    processed_segment = None

    def toString(self, include_spkid: bool = False, spk_sep: str = ":"):
        output = f"{self.speaker_id}{spk_sep} " if include_spkid and self.speaker_id is not None else ""
        return output + (self.raw_segment if self.processed_segment is None else self.processed_segment)
    
    @property
    def raw_segment(self) -> str:
        return " ".join([w.word for w in self.words]).strip()

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
            "raw_segment": self.raw_segment,
            "segment" : self.processed_segment if self.processed_segment is not None else self.raw_segment,
            "words": [w.json for w in self.words]
        }

class TranscriptionResult:
    """ Transcription result manages transcription results, post-processing and formating for transcription results."""
    
    def __init__(self, transcriptions: List[Tuple[dict, float]], config: TranscriptionConfig):
        """ Initialisation accepts list of tuple (transcription, time_offset) """
        self.transcription_confidence = 0.0
        self.words = []
        self.segments = []

        self.config = config
        self._mergeTranscription(transcriptions)

    def _mergeTranscription(self, transcriptions: List[Tuple[dict, float]]):
        """ Merges transcription results applying offsets """
        for transcription, offset in transcriptions:
            for w in transcription["words"]:
                word = Word(**w)
                word.apply_offset(offset)
                self.words.append(word)
            self.transcription_confidence += transcription["confidence-score"]
        self.transcription_confidence /= len(transcriptions)
        self.words.sort(key=lambda x: x.start)
        
    def setDiarizationResult(self, diarizationResult: Union[str, dict]):
        """ Convert word data into speech segments using diarization data"""
        diarization_data = json.loads(diarizationResult) if isinstance(diarizationResult, str) else diarizationResult
        self.words.sort(key=lambda x: x.start)

        segments = sorted(diarization_data["segments"], key=lambda x: x["seg_begin"])
        
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
    
    def setNoDiarization(self):
        """ Convert word data into a speech segment when there is no diarization """
        self.segments.append(SpeechSegment(None, self.words))

    def setProcessedSegment(self, processed_segments: Union[List[str], str]):
        """ Add the processed_segment value to segments"""
        if type(processed_segments) == str:
            processed_segments = [processed_segments]
        for seg, proc_seg in zip(self.segments, processed_segments):
            seg.processed_segment = proc_seg
    
    @property
    def final_transcription(self) -> str:
        return "\n".join([seg.toString(include_spkid=True) for seg in self.segments]).strip()
    
    @property
    def raw_transcription(self) -> str:
        return " ".join([w.word for w in self.words]).strip()

    def final_result(self) -> dict:
        result = dict()
        result["transcription_result"] = self.final_transcription
        result["raw_transcription"] = self.raw_transcription
        result["confidence"] = self.transcription_confidence
        result["segments"] = [s.json for s in self.segments]
        return result