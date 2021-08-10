from pymongo import MongoClient

class DBClient:
    def __init__(self, db_info: dict):
        self.isset = False
        if self.check_params(db_info):
            self.client = MongoClient(db_info["db_host"], port=db_info["db_port"])
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
                         param: str):
        """ Check if a result already exist for the request in a mongo database"""
        print(file_hash, param)
        if not self.isset:
            raise Exception("DB Client is not set.")
        entry = self.collection.find_one({"_id" : file_hash})
        if entry is None:
            return None
        if param in entry.keys():
            return entry[param]
        return None

    def write_result(self, hash: str, output_format:str, result):
        """ Write result in db """
        if not self.isset:
            raise Exception("DB Client is not set.")
        self.collection.find_one_and_update({"_id": hash},
                                            {"$set": {output_format: result}}, upsert=True)

    def close(self):
        """ Close client connexion """
        if self.isset:
            self.client.close()