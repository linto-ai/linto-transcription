from pymongo import MongoClient

__all__ = ["check_for_result"]

def check_for_result(db_info: dict, 
                     file_hash: str, 
                     param: str):
    """ Check if a result already exist for the request in a mongo database"""
    print(db_info, file_hash, param)
    client = MongoClient(db_info["db_host"], port=db_info["db_port"])
    collection = client[db_info["db_name"]][db_info["service_name"]]
    entry = collection.find_one({"_id" : file_hash})
    client.close()
    if entry is None:
        return None
    if param in entry.keys():
        return entry[param]
    return None
