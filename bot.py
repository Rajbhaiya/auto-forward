import time
import logging
from pyrogram import Client, filters, idle
from datetime import datetime
import pymongo
import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
    level=logging.INFO
)
logger = logging.getLogger("Auto-Forwarder-Bot")
scheduler = AsyncIOScheduler()
# Your Telegram bot token
API_ID = 13675555  # Replace with your API ID
API_HASH = "c0da9c346d2c45dbc7ec49a05da9b2b6"  # Replace with your API hash
TOKEN = "6680969743:AAHpx2FWxrJDDBZTasyyUk05h7a0zG6aeMc"

app = Client("Auto-Forwarder-Bot", api_id=API_ID, api_hash=API_HASH, bot_token=TOKEN)


mongodb_client = pymongo.MongoClient("mongodb+srv://kagut:kagut@cluster0.hol7gj5.mongodb.net/?retryWrites=true&w=majority", 27017) 
db = mongodb_client["channel_scheduler"]
channels_col = db["channels"]


def add_channel(main_channel, destination_channel, schedule_time):
    channel_data = {
        "main_channel": main_channel,
        "destination_channel": destination_channel,
        "schedule_time": schedule_time
    }
    channels_col.insert_one(channel_data)


def remove_channel(main_channel, destination_channel, schedule_time):
    channels_col.delete_one({"main_channel": main_channel, "destination_channel": destination_channel, "schedule_time": schedule_time})


@app.on_message(filters.channel)
async def forward_messages(client, message):
    if not channels_col.find_one({"main_channel": message.chat.id}):
        return
    for channel_data in channels_col.find({"main_channel": message.chat.id}):
        destination_channel_id = channel_data["destination_channel"]
        hour, minute = map(int, channel_data["schedule_time"].split(":"))
        current_time = datetime.now(pytz.timezone("Asia/Kolkata"))
        schedule_time = current_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
        scheduler.add_job(app.copy_message, "date", run_date=schedule_time, args=(destination_channel_id, message.chat.id, message.id), kwargs={"reply_markup": message.reply_markup})


@app.on_message(filters.command("addchannel"))
async def add_channel_command(client, message):
    if len(message.command) != 4:
        await message.reply_text("Usage: /addchannel main_channel_id destination_channel_id HH:MM")
        return

    main_channel = int(message.command[1])
    destination_channel = int(message.command[2])
    schedule_time = message.command[3]
    hour, minute = map(int, schedule_time.split(":"))

    add_channel(main_channel, destination_channel, schedule_time)
    await message.reply_text("Channel added to the database.")

@app.on_message(filters.command("listchannels"))
async def list_channels_command(client, message):
    channels = channels_col.find()
    channel_list = ["Channels in the database:"]
    for channel in channels:
        channel_list.append(f"> Main: `{channel['main_channel']}`\n> Destination: `{channel['destination_channel']}`\n> Schedule Time: `{channel['schedule_time']}`")
    await message.reply_text("\n\n".join(channel_list))

@app.on_message(filters.command("removechannel"))
async def remove_channel_command(client, message):
    if len(message.command) != 3:
        await message.reply_text("Usage: /removechannel main_channel_id destination_channel_id HH:MM")
        return

    main_channel = int(message.command[1])
    destination_channel = int(message.command[2])
    schedule_time = message.command[3]

    remove_channel(main_channel, destination_channel, schedule_time)
    await message.reply_text("Channel removed from the database.")

@app.on_message(filters.command("start"))
async def start_command(client, message):
    await message.reply_text("""Namaste i'm a auto forward robot. You can schedule your posts through me. Check commands below to know how to set schedule.
    
1. /addchannel : To add channels for autoforward posts with schedule.
2. /removechannel : To remove added channel from database. 
3 /listchannels :  Check all added channel.""")

if __name__ == "__main__":
    scheduler.start()
    app.start()
    logger.info("Bot started. Idling...")
    idle()
    app.stop()
    logger.info("Bot stopped.")
