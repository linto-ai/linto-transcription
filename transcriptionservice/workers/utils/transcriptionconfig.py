from typing import Union
import json

class Config:
    _keys_default = {}
    def __init__(self, config: Union[str, dict] = {}):
        if type(config) is str:
            try:
                config = json.loads(config)
            except Exception as e:
                raise Exception("Failed to load transcription config")
        self._loadConfig(config)
        self._checkConfig()
    
    def _loadConfig(self, config: dict):
        for key in self._keys_default.keys():
            self.__setattr__(key, config.get(key, self._keys_default[key]))
    
    def _checkConfig(self):
        """ Check uncompatible field values """
        pass
    
    def toJson(self) -> dict:
        """ Returns configuration as a dictionary """ 
        config_dict  = {}
        for key in self._keys_default.keys():
            config_dict[key] = self.__getattribute__(key) if not isinstance(self.__getattribute__(key), Config) else self.__getattribute__(key).toJson()
        return config_dict

    def __eq__(self, other):
        """ Compares 2 Config. Returns true if all fields are the same """
        if isinstance(other, Config):
            for key in self._keys_default.keys():
                try:
                    if self.__getattribute__(key) != other.__getattribute__(key):
                        return False
                except:
                    return False
            return True
        return False
                             
    def __str__(self) -> str:
        return json.dumps(self.toJson())

class DiarizationConfig(Config):
    """ DiarizationConfig parses and holds diarization related configuration.
    Expected configuration format is as follows:
    ```json
    {
      "enableDiarization": boolean (false),
      "numberOfSpeaker": integer (null),
      "maxNumberOfSpeaker": integer (null)
    }
    ```
    """
    _keys_default = {"enableDiarization" : False,
                     "numberOfSpeaker": None,
                     "maxNumberOfSpeaker": None}
    def __init__(self, config: Union[str, dict] = {}):
        super().__init__(config)
        self._checkConfig()

    def _checkConfig(self):
        if self.enableDiarization in ["true", 1, True] :
            self.enableDiarization = True
            if type(self.numberOfSpeaker) is int:
                if self.numberOfSpeaker <=0:
                    self.numberOfSpeaker = None
                elif self.numberOfSpeaker == 1:
                    self.enableDiarization = False
                    return

            if type(self.maxNumberOfSpeaker) is int:
                if self.numberOfSpeaker is not None:
                    self.maxNumberOfSpeaker = self.numberOfSpeaker
                else:
                    if self.maxNumberOfSpeaker <= 0:
                        self.maxNumberOfSpeaker = None
        else:
            self.enableDiarization = False


class TranscriptionConfig(Config):
    """ TranscriptionConfig parses and holds transcription request configuration.
    Expected configuration format is as follows:
    ```json
    {
      "transcribePerChannel": boolean (false),
      "enablePunctuation": boolean (false),
      "enableDiarization": boolean (false),
      "diarizationConfig": object DiarizationConfig (null), 
    }
    ```
    """
    _keys_default = {"transcribePerChannel" : False, 
                     "enablePunctuation" : False, 
                     "enableDiarization" : False,
                     "diarizationConfig" : DiarizationConfig()}
    
    def __init__(self, config: Union[str, dict] = {}):
        super().__init__(config)

    def __eq__(self, other):
        if isinstance(other, TranscriptionConfig):
            for key in self._keys_default.keys():
                if self.__getattribute__(key) != other.__getattribute__(key):
                    return False
            return True
        return False
                             
    def __str__(self) -> str:
        return json.dumps(self.toJson())
