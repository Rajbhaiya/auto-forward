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

def add_channel(main_channel, destination_channel, schedule_time, post_delay_hours, post_delay_minutes):
    channel_data = {
        "main_channel": main_channel,
        "destination_channel": destination_channel,
        "schedule_time": schedule_time,
        "post_delay_hours": post_delay_hours,
        "post_delay_minutes": post_delay_minutes
    }
    channels_col.insert_one(channel_data)

def remove_channel(main_channel, destination_channel, schedule_time):
    channels_col.delete_one({"main_channel": main_channel, "destination_channel": destination_channel, "schedule_time": schedule_time})

def forward_delayed_messages():
    current_time = datetime.now(pytz.timezone("Asia/Kolkata"))
    for channel_data in channels_col.find():
        destination_channel_id = channel_data["destination_channel"]
        schedule_time = datetime.strptime(channel_data["schedule_time"], "%H:%M")
        post_delay_hours = channel_data["post_delay_hours"]
        post_delay_minutes = channel_data["post_delay_minutes"]

        time_difference = (current_time - schedule_time).total_seconds() / 60
        if time_difference >= (post_delay_hours * 60 + post_delay_minutes):
            main_channel_id = channel_data["main_channel"]
            message = app.get_messages(main_channel_id, limit=1).pop()
            app.send_message(destination_channel_id, text=message.text)
            remove_channel(main_channel_id, destination_channel_id, channel_data["schedule_time"])

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
    if len(message.command) != 5:
        await message.reply_text("Usage: /addchannel main_channel_id destination_channel_id HH:MM post_delay_hours post_delay_minutes")
        return

    main_channel = int(message.command[1])
    destination_channel = int(message.command[2])
    schedule_time = message.command[3]
    post_delay_hours = int(message.command[4])
    post_delay_minutes = int(message.command[5])

    add_channel(main_channel, destination_channel, schedule_time, post_delay_hours, post_delay_minutes)
    await message.reply_text("Channel added to the database.")

@app.on_message(filters.command("listchannels"))
async def list_channels_command(client, message):
    channels = channels_col.find()
    channel_list = ["Channels in the database:"]
    for channel in channels:
        channel_list.append(f"> Main: `{channel['main_channel']}`\n> Destination: `{channel['destination_channel']}`\n> Schedule Time: `{channel['schedule_time']}`\n> Post Delay: {channel['post_delay_hours']} hours {channel['post_delay_minutes']} minutes")
    await message.reply_text("\n\n".join(channel_list)

@app.on_message(filters.command("removechannel"))
async def remove_channel_command(client, message):
    if len(message.command) != 4:
        await message.reply_text("Usage: /removechannel main_channel_id destination_channel_id HH:MM")
        return

    main_channel = int(message.command[1])
    destination_channel = int(message.command[2])
    schedule_time = message.command[3]

    remove_channel(main_channel, destination_channel, schedule_time)
    await message.reply_text("Channel removed from the database.")

@app.on_message(filters.command("delay_post"))
async def delay_post_command(client, message):
    if len(message.command) != 4:
        await message.reply_text("Usage: /delay_post main_channel_id destination_channel_id delay_hours delay_minutes")
        return

    main_channel = int(message.command[1])
    destination_channel = int(message.command[2])
    delay_hours = int(message.command[3])
    delay_minutes = int(message.command[4])

    current_time = datetime.now(pytz.timezone("Asia/Kolkata"))
    schedule_time = current_time + timedelta(hours=delay_hours, minutes=delay_minutes)
    schedule_time_str = schedule_time.strftime("%H:%M")

    add_channel(main_channel, destination_channel, schedule_time_str, delay_hours, delay_minutes)
    await message.reply_text(f"Post scheduled with a {delay_hours} hours and {delay_minutes} minutes delay.")

@app.on_message(filters.command("remove_delay_post"))
async def remove_delay_post_command(client, message):
    if len(message.command) != 3:
        await message.reply_text("Usage: /remove_delay_post main_channel_id destination_channel_id HH:MM")
        return

    main_channel = int(message.command[1])
    destination_channel = int(message.command[2])
    schedule_time = message.command[3]

    remove_channel(main_channel, destination_channel, schedule_time)
    await message.reply_text("Delayed post removed from the database.")

if __name__ == "__main__":
    scheduler.add_job(forward_delayed_messages, "interval", minutes=1)  # Check every minute
    scheduler.start()
    app.start()
    logger.info("Bot started. Idling...")
    idle()
    app.stop()
    logger.info("Bot stopped.")
