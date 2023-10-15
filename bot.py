import time
import logging
from pyrogram import Client, filters, idle
from datetime import datetime, timedelta
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

def readable_time(seconds: int) -> str:
    count = 0
    ping_time = ""
    time_list = []
    time_suffix_list = ["s", "m", "h", "days"]

    while count < 4:
        count += 1
        if count < 3:
            remainder, result = divmod(seconds, 60)
        else:
            remainder, result = divmod(seconds, 24)
        if seconds == 0 and remainder == 0:
            break
        time_list.append(int(result))
        seconds = int(remainder)

    for x in range(len(time_list)):
        time_list[x] = str(time_list[x]) + time_suffix_list[x]
    if len(time_list) == 4:
        ping_time += time_list.pop() + ", "

    time_list.reverse()
    ping_time += ":".join(time_list)

    return ping_time


@app.on_message(filters.channel)
async def forward_messages(client, message):
    if not channels_col.find_one({"main_channel": message.chat.id}):
        return
    for channel_data in channels_col.find({"main_channel": message.chat.id}):
        destination_channel_id = channel_data["destination_channel"]
        current_time = datetime.now(pytz.timezone("Asia/Kolkata"))
        if channel_data.get("schedule_time"):
            hour, minute = map(int, channel_data["schedule_time"].split(":"))
            schedule_time = current_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
            scheduler.add_job(app.copy_message, "date", run_date=schedule_time, args=(destination_channel_id, message.chat.id, message.id), kwargs={"reply_markup": message.reply_markup})
        if channel_data.get("delay_time"):
            schedule_time = current_time + timedelta(seconds=int(channel_data["delay_time"]))
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

    add_channel(main_channel, destination_channel, schedule_time, None)
    await message.reply_text("Channel added to the database.")

@app.on_message(filters.command("adddelay"))
async def add_delay_command(client, message):
    if len(message.command) != 4:
        await message.reply_text("Usage: /adddelay main_channel_id destination_channel_id delay_time(in seconds).")
        return

    main_channel = int(message.command[1])
    destination_channel = int(message.command[2])
    delay_time = int(message.command[3])

    add_channel(main_channel, destination_channel, None, delay_time)
    await message.reply_text(f"Channel added to the database with a delay time of {readable_time(delay_time)}.")


@app.on_message(filters.command("removedelay"))
async def remove_delay_command(client, message):
    if len(message.command) != 4:
        await message.reply_text("Usage: /removedelay main_channel_id destination_channel_id delay_time(in seconds).")
        return

    main_channel = int(message.command[1])
    destination_channel = int(message.command[2])
    delay_time = int(message.command[3])

    remove_channel_delay(main_channel, destination_channel, delay_time)
    await message.reply_text("Channel delay removed from the database.")


@app.on_message(filters.command("removechannel"))
async def remove_channel_command(client, message):
    if len(message.command) != 4:
        await message.reply_text("Usage: /removechannel main_channel_id destination_channel_id HH:MM")
        return

    main_channel = int(message.command[1])
    destination_channel = int(message.command[2])
    schedule_time = message.command[3]
    hour, minute = map(int, schedule_time.split(":"))

    remove_channel_schedule(main_channel, destination_channel, schedule_time)
    await message.reply_text("Channel schedule removed from the database.")

@app.on_message(filters.command("listchannels"))
async def list_channels_command(client, message):
    channels = channels_col.find()
    channel_list = ["Channels in the database:"]
    for channel in channels:
        channel_list.append(f"> Main: `{channel['main_channel']}`\n> Destination: `{channel['destination_channel']}`\n> Schedule Time: `{channel.get('schedule_time')}`\n>Delay Time: `{readable_time(channel.get('delay_time', 0))}")
    await message.reply_text("\n\n".join(channel_list))


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
