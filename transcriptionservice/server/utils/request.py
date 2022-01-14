from typing import Union
import json

class TranscriptionConfig:
    """ TranscriptionConfig parses transcription request configuration.
    Expected configuration format is as followed:
    ```json
    {
      "transcribePerChannel": boolean (false),
      "enablePunctuation": boolean (false), 
      "enableDiarization": boolean (false), 
      "diarizationSpeakerCount": integer (null), 
      "forceSync": boolean (false),
      "noCache" : boolean (false),
      "returnPart" : boolean (false)
    }
    ```
    """
    _keys_default = {"transcribePerChannel" : False, 
                     "enablePunctuation" : False, 
                     "enableDiarization" : False,  
                     "forceSync" : False, 
                     "noCache", : False, 
                     "returnPart": False,
                     "diarizationSpeakerCount" : None,}
    
    def __init__(self, requestConfig: Union[str, dict] = {}, returnJSON: bool = False):
        if type(requestConfig) is str:
            try:
                requestConfig = json.loads(requestConfig)
            except Exception as e:
                raise Exception("Failed to load transcription config")
        self._loadConfig(requestConfig)
        self.returnJSON = returnJson
    
    def _loadConfig(self, config: dict):
        for key, self._keys_default.keys():
            self.__setattr__(key, config.get(key, self._keys_default[key]))
    
    def jsonConfig(self) -> dict:
        """ Returns configuration as a dictionary """ 
        config_dict  = {}
        for key, default_value in zip(self._keys, self._default_values):
            config_dict[key] = self.__getattribute__(key)
        config_dict["return_json"] = self.returnJSON
        return config_dict
                             
    def __str__(self) -> str:
        return json.dumps(self.jsonConfig())

    def formatKey(self) -> str:
        """ Format key for result storage purpose"""
        format_key = "".join([int(self.__getattribute__(k)) for k in self._keys_default.keys()[:-1]])
        format_key += f"{self.diarizationSpeakerCount}"

class TranscriptionResponse:
    def __init__(self):
        pass
    