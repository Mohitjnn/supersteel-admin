from pymongo import MongoClient
from gridfs import GridFSBucket
from dotenv import load_dotenv
import os

load_dotenv()

MONGO_CONNECTION_NAME = os.environ.get("MONGO_CONNECTION_URL")
MONGO_DB = os.environ.get("MONGO_DB")
MONGO_BUCKET_NAME = os.environ.get("MONGO_BUCKET_NAME")

client = MongoClient(MONGO_CONNECTION_NAME)
db = client[MONGO_DB]
bucket = GridFSBucket(db, bucket_name=MONGO_BUCKET_NAME)


def get_db():
    return db


def get_bucket():
    return bucket


def serialize_list(cursor):
    """
    Serialize a MongoDB cursor to a list of dictionaries.
    """
    return [document for document in cursor]
