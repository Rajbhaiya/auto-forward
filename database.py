import asyncio
import sys
import logging
from motor import motor_asyncio
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

MONGO_DB_URI="mongodb+srv://kagut:kagut@cluster0.hol7gj5.mongodb.net/?retryWrites=true&w=majority"
MONGO_PORT = 27017
MONGO_DB = "channel_scheduler"


client = MongoClient()
client = MongoClient(MONGO_DB_URI, MONGO_PORT)[MONGO_DB]
motor = motor_asyncio.AsyncIOMotorClient(MONGO_DB_URI, MONGO_PORT)
db = motor[MONGO_DB]
db = client["channel_scheduler"]
try:
    asyncio.get_event_loop().run_until_complete(motor.server_info())
except ServerSelectionTimeoutError:
    sys.exit(logging.critical("Can't connect to mongodb! Exiting..."))

# Create a collection to store channel information
channel_collection = db["channels"]
