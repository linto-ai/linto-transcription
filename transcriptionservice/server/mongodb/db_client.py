from pymongo import MongoClient
from transcriptionservice.workers.utils import TranscriptionConfig, TranscriptionResult

class DBClient:
    """ DBClient setups and maintains a connexion to a MongoDB database """
    def __init__(self, db_info: dict):
        """ db_info object is a dictionary structured as follow:
            {
               "db_host" : database host, 
               "db_port" : database listening port, 
               "service_name" : service name used as collection name, 
               "db_name": database's name
            }     
        """
        self.isset = False
        if self.check_params(db_info):
            self.client = MongoClient(db_info["db_host"], port=db_info["db_port"], connect=False)
            self.collection = self.client[db_info["db_name"]][db_info["service_name"]]
            self.isset = True

    def check_params(self, db_info: dict) -> bool:
        """ Check db_parameters """
        for k in db_info.keys():
            if db_info[k] is None:
                return False
        return True

    def check_for_result(self,
                         file_hash: str,
                         config: TranscriptionConfig):
        """ Check if a result already exist for the request in a mongo database"""
        if not self.isset:
            raise Exception("DB Client is not set.")
        entry = self.collection.find_one({"_id" : file_hash})
        if entry is None:
            return None
        stored_config = entry["config"]
        return entry["result"] if stored_config == config.toJson() else None
    
    def check_for_jobid(self, job_id: str):
        if not self.isset:
            raise Exception("DB Client is not set.")
        entry = self.collection.find_one({"jobid": job_id})
        if entry is None:
            return None
        return entry["result"]
        
        
    def write_result(self, file_hash: str, job_id: str, config: TranscriptionConfig, result: TranscriptionResult):
        """ Write result in db """
        if not self.isset:
            raise Exception("DB Client is not set.")
        self.collection.find_one_and_update({"_id": file_hash},
                                            {"$set": {"jobid": job_id,
                                                      "config": config.toJson(),
                                                      "result" : result.final_result()}}, upsert=True)

    def close(self):
        """ Close client connexion """
        if self.isset:
            self.client.close()