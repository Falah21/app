import os
from pymongo import MongoClient

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = "e_arsip"

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

users_col = db["users"]
docs_col = db["documents"]
categories_col = db["categories"]
