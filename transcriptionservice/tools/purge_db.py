import os

from pymongo import MongoClient

if __name__ == "__main__":
    client = MongoClient(os.environ.get("MONGO_HOST"), port=int(os.environ.get("MONGO_PORT")))
    collection = client["transcriptiondb"][os.environ.get("SERVICE_NAME")]
    collection.drop()
