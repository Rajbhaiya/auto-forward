import asyncio
import schedule
import logging
from datetime import datetime as dt
import time
import pytz
from pyrogram import Client, filters
from pymongo import MongoClient
from telegram import Bot, Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# Your Telegram bot token
TELEGRAM_TOKEN = "6680969743:AAHpx2FWxrJDDBZTasyyUk05h7a0zG6aeMc"
MONGO_URI = "mongodb+srv://kagut:kagut@cluster0.hol7gj5.mongodb.net/?retryWrites=true&w=majority"
db = None

# Create a MongoDB client and database
mongo_client = MongoClient(MONGO_URI, 27017)
db = mongo_client.get_database("channel_scheduler")

# Initialize logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the Telegram bot
bot = Bot(TELEGRAM_TOKEN)

def get_channels(db):
    channels = db["channels"]
    return channels.find()


# Function to add a channel to the database
def add_channel(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    args = context.args

    if len(args) != 3:
        update.message.reply_text("Usage: /addchannel main_channel destination_channel HH:MM")
        return

    main_channel = args[0]
    destination_channel = args[1]
    schedule_time = args[2]

    # Store channel information in the database
    channels = db.channels
    channels.insert_one({
        "main_channel": main_channel,
        "destination_channel": destination_channel,
        "schedule_time": schedule_time
    })

    update.message.reply_text("Channel added successfully.")

# Function to list added channels
def list_channels(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id

    channels = db.channels.find()
    channel_list = []

    for channel in channels:
        channel_list.append(
            f"Main Channel: {channel['main_channel']}, Destination Channel: {channel['destination_channel']}, Schedule Time: {channel['schedule_time']}"
        )

    if channel_list:
        update.message.reply_text("Channels:\n" + "\n".join(channel_list))
    else:
        update.message.reply_text("No channels added yet.")

# Function to remove a channel from the database
def remove_channel(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    args = context.args

    if len(args) != 2:
        update.message.reply_text("Usage: /removechannel main_channel destination_channel")
        return

    main_channel = args[0]
    destination_channel = args[1]

    # Remove the specified channel
    result = db.channels.delete_one({
        "main_channel": main_channel,
        "destination_channel": destination_channel
    })

    if result.deleted_count > 0:
        update.message.reply_text("Channel removed successfully.")
    else:
        update.message.reply_text("Channel not found in the database.")

# Function to forward messages from main to destination channels
def forward_messages():
    global db  # Access the global variable for the database
    if db is None:
        db = create_database()

    channels = get_channels(db)
    current_time = datetime.now(pytz.timezone("Asia/Kolkata"))
    current_time_str = current_time.strftime("%H:%M")

    for channel in channels:
        main_channel_id = channel['main_channel']
        destination_channel_id = channel['destination_channel']
        schedule_time = channel['schedule_time']

        if current_time_str == schedule_time:
            main_channel = context.bot.get_chat(main_channel_id)
            destination_channel = context.bot.get_chat(destination_channel_id)
            last_message = context.bot.get_chat(main_channel_id).get_last_message()

            if last_message:
                message_id = last_message.message_id
                context.bot.forward_message(destination_channel_id, main_channel_id, message_id)
# Function to start the bot
def start(update: Update, context: CallbackContext):
    update.message.reply_text("Bot is running. Use /addchannel, /removechannel, or /listchannels to manage channels.")

# Main function to run the bot
def main():
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("addchannel", add_channel, pass_args=True))
    dispatcher.add_handler(CommandHandler("removechannel", remove_channel, pass_args=True))
    dispatcher.add_handler(CommandHandler("listchannels", list_channels))

    updater.start_polling()

    schedule.every().minute.at(":00").do(forward_messages)
    schedule.every().minute.at(":30").do(forward_messages)

    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()
