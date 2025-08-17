# db.py
from pymongo import MongoClient

# Ubah sesuai kebutuhan: bisa ke remote MongoDB Atlas atau mongodb lokal
MONGO_URI = "mongodb+srv://ahmadihdafalah:amdryzen1010@cluster0.10a3ead.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DB_NAME = "e_arsip"

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

users_col = db["users"]
docs_col = db["documents"]
categories_col = db["categories"]
