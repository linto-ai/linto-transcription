import json
from typing import Union

from transcriptionservice.transcription.configs.sharedconfig import Config
from transcriptionservice.transcription.configs.taskconfig import (
    DiarizationConfig, PunctuationConfig)


class TranscriptionConfig(Config):
    """TranscriptionConfig parses and holds transcription request configuration.
    Expected configuration format is as follows:
    ```json
    {
      "transcribePerChannel": boolean (false),
      "enablePunctuation": boolean (false),
      "enableDiarization": boolean (false),
      "diarizationConfig": object DiarizationConfig (null),
      "punctuationConfig": object PunctuationConfig(null)
    }
    ```
    """

    _keys_default = {
        "transcribePerChannel": False,
        "enablePunctuation": False,  # Kept for backward compatibility
        "diarizationConfig": DiarizationConfig(),
        "punctuationConfig": PunctuationConfig(),
    }

    def __init__(self, config: Union[str, dict] = {}):
        super().__init__(config)
        self._checkConfig()

    @property
    def tasks(self) -> list:
        return [self.diarizationConfig, self.punctuationConfig]

    def _checkConfig(self):
        """Check and update field values"""
        if isinstance(self.diarizationConfig, dict):
            self.diarizationConfig = DiarizationConfig(self.diarizationConfig)
        if isinstance(self.punctuationConfig, dict):
            self.punctuationConfig = PunctuationConfig(self.punctuationConfig)

        if self.enablePunctuation:
            self.punctuationConfig.enablePunctuation = True

    def __eq__(self, other):
        if isinstance(other, TranscriptionConfig):
            for key in self._keys_default.keys():
                if self.__getattribute__(key) != other.__getattribute__(key):
                    return False
            return True
        return False

    def __str__(self) -> str:
        return json.dumps(self.toJson())
