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

# Constants
TELEGRAM_TOKEN = "6680969743:AAHpx2FWxrJDDBZTasyyUk05h7a0zG6aeMc"  # Replace with your bot token
MONGO_URI = "mongodb+srv://kagut:kagut@cluster0.hol7gj5.mongodb.net/?retryWrites=true&w=majority"   # Replace with your MongoDB connection URI

# Initialize logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name)

# Create a MongoDB client and database
class Database:
    def __init__(self, uri):
        self.client = MongoClient(uri)
        self.db = self.client.get_database("channel_scheduler")

    def add_channel(self, main_channel, destination_channel, schedule_time):
        channels = self.db["channels"]
        channels.insert_one({
            "main_channel": main_channel,
            "destination_channel": destination_channel,
            "schedule_time": schedule_time
        })

    def list_channels(self):
        channels = self.db["channels"]
        return channels.find()

    def remove_channel(self, main_channel, destination_channel):
        result = self.db["channels"].delete_one({
            "main_channel": main_channel,
            "destination_channel": destination_channel
        })
        return result.deleted_count > 0

    def get_channels(self):
        channels = self.db["channels"]
        return channels.find()

# Telegram bot class
class TelegramBot:
    def __init__(self, token):
        self.bot = Bot(token)
        self.updater = Updater(token, use_context=True)
        self.dispatcher = self.updater.dispatcher

    def add_channel(self, update, context):
        chat_id = update.message.chat_id
        args = context.args

        if len(args) != 3:
            update.message.reply_text("Usage: /addchannel main_channel destination_channel HH:MM")
            return

        main_channel = args[0]
        destination_channel = args[1]
        schedule_time = args[2]

        db.add_channel(main_channel, destination_channel, schedule_time)
        update.message.reply_text("Channel added successfully.")

    def list_channels(self, update, context):
        chat_id = update.message.chat_id

        channels = db.list_channels()
        channel_list = []

        for channel in channels:
            channel_list.append(
                f"Main Channel: {channel['main_channel']}, Destination Channel: {channel['destination_channel']}, Schedule Time: {channel['schedule_time']}"
            )

        if channel_list:
            update.message.reply_text("Channels:\n" + "\n".join(channel_list))
        else:
            update.message.reply_text("No channels added yet.")

    def remove_channel(self, update, context):
        chat_id = update.message.chat_id
        args = context.args

        if len(args) != 2:
            update.message.reply_text("Usage: /removechannel main_channel destination_channel")
            return

        main_channel = args[0]
        destination_channel = args[1]

        if db.remove_channel(main_channel, destination_channel):
            update.message.reply_text("Channel removed successfully.")
        else:
            update.message.reply_text("Channel not found in the database.")

    def start(self, update, context):
        update.message.reply_text("Bot is running. Use /addchannel, /removechannel, or /listchannels to manage channels.")

    def run(self):
        self.dispatcher.add_handler(CommandHandler("start", self.start))
        self.dispatcher.add_handler(CommandHandler("addchannel", self.add_channel, pass_args=True))
        self.dispatcher.add_handler(CommandHandler("removechannel", self.remove_channel, pass_args=True))
        self.dispatcher.add_handler(CommandHandler("listchannels", self.list_channels))

        self.updater.start_polling()
        schedule.every().minute.at(":00").do(forward_messages)
        schedule.every().minute.at(":30").do(forward_messages)

        while True:
            schedule.run_pending()
            time.sleep(1)

# Function to forward messages from main to destination channels
def forward_messages():
    current_time = dt.now(pytz.timezone("Asia/Kolkata"))
    current_time_str = current_time.strftime("%H:%M")

    for channel in db.get_channels():
        main_channel_id = channel['main_channel']
        destination_channel_id = channel['destination_channel']
        schedule_time = channel['schedule_time']

        if current_time_str == schedule_time:
            main_channel = bot.bot.get_chat(main_channel_id)
            destination_channel = bot.bot.get_chat(destination_channel_id)
            last_message = bot.bot.get_chat(main_channel_id).get_last_message()

            if last_message:
                message_id = last_message.message_id
                bot.bot.forward_message(destination_channel_id, main_channel_id, message_id)

if __name__ == "__main__":
    db = Database(MONGO_URI)
    bot = TelegramBot(TELEGRAM_TOKEN)
    bot.run()
