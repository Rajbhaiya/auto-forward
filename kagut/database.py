import asyncio
import sys
import logging
import pymongo
import motor
from pymongo.errors import ServerSelectionTimeoutError
from motor import motor_asyncio
from dotenv import load_dotenv

load_dotenv('.env', override=True)

MONGO_URI = "mongodb+srv://kagut:kagut@cluster0.hol7gj5.mongodb.net/?retryWrites=true&w=majority"

mongodb_client = pymongo.MongoClient(MONGO_URI, 27017) 
db = mongodb_client["kagut"]
channels_col = db["post_channels"]

try:
    asyncio.get_event_loop().run_until_complete(motor.server_info())
except ServerSelectionTimeoutError:
    sys.exit(logging.critical("Can't connect to mongodb! Exiting..."))


def add_channel(main_channel, destination_channel, schedule_time, delay_time):
    channel_data = {
        "main_channel": main_channel,
        "destination_channel": destination_channel,
    }
    timing_data = {
        "schedule_time": schedule_time,
        "delay_time": delay_time,
    }
    channels_col.update_one(channel_data, {"$set": timing_data}, upsert=True)


def remove_channel_schedule(main_channel, destination_channel,):
    channel_data = {"main_channel": main_channel, "destination_channel": destination_channel}
    db_item = channels_col.find_one(channel_data)
    if db_item:
        if db_item.get("schedule_time"):
            channels_col.update_one(channel_data, {"$set": {"schedule_time": None}})
        else:
            channels_col.delete_one(db_item)

def remove_channel_schedule(main_channel, destination_channel,):
    channel_data = {"main_channel": main_channel, "destination_channel": destination_channel}
    db_item = channels_col.find_one(channel_data)
    if db_item:
        if db_item.get("delay_time"):
            channels_col.update_one(channel_data, {"$set": {"delay_time": None}})
        else:
            channels_col.delete_one(db_item)
