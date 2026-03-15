import os
from pymongo import MongoClient

# Use local mongdb by default
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = "astramind_db"

client = None
db = None

def get_db():
    global client, db
    if client is None:
        try:
            client = MongoClient(MONGO_URI)
            db = client[DB_NAME]
            print("Connected to MongoDB")
        except Exception as e:
            print(f"Error connecting to MongoDB: {e}")
            client = None
            db = None
    return db
