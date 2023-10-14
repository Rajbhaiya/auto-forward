import schedule
import time
from pyrogram import Client
from datetime import datetime
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from pymongo import MongoClient
import pytz

# Your Telegram bot token
API_ID = 13675555
API_HASH = "c0da9c346d2c45dbc7ec49a05da9b2b6"
TOKEN = "6680969743:AAHpx2FWxrJDDBZTasyyUk05h7a0zG6aeMc"

# MongoDB connection
MONGO_URI = "mongodb+srv://f2l:f2l@cluster0.fjjge1y.mongodb.net/?retryWrites=true&w=majority:27017"  # Update with your MongoDB URI
DB_NAME = "channel_scheduler"

# Create a MongoDB client
client = MongoClient(MONGO_URI)
db = client[DB_NAME]

# Create a collection to store channel information
channel_collection = db["channels"]

# Initialize the Telegram bot
bot = Client("autoforward", api_id=API_ID, api_hash=API_HASH, bot_token=TOKEN)


# Command to add a main channel, destination channel, and schedule time
def add_channels(update: Update, context: CallbackContext):
  if len(context.args) != 3:
    update.message.reply_text(
        "Usage: /addchannels @main_channel @destination_channel HH:MM")
    return

  main_channel = context.args[0]
  destination_channel = context.args[1]
  schedule_time = context.args[2]

  # Check if both channels exist and are channels
  main_chat_type = bot.get_chat(main_channel).type
  dest_chat_type = bot.get_chat(destination_channel).type

  if main_chat_type != "channel" or dest_chat_type != "channel":
    update.message.reply_text("Both provided channels must be valid channels.")
    return

  # Check if the combination of main and destination channels is unique
  if channel_collection.find_one({
      "main_channel": main_channel,
      "destination_channel": destination_channel
  }):
    update.message.reply_text("This channel pair is already in the database.")
    return

  # Add the channel pair and schedule time to the database
  channel_collection.insert_one({
      "main_channel": main_channel,
      "destination_channel": destination_channel,
      "schedule_time": schedule_time
  })
  update.message.reply_text(f"Channel pair added to the database.")


# Function to send scheduled messages to destination channels
def send_scheduled_messages():
  current_time = datetime.now(pytz.timezone("Asia/Kolkata"))
  current_time_str = current_time.strftime("%H:%M")

  for channel_info in channel_collection.find():
    main_channel = channel_info["main_channel"]
    dest_channel = channel_info["destination_channel"]
    scheduled_time = channel_info["schedule_time"]

    if current_time_str == scheduled_time:
      message = f"Scheduled message for {dest_channel} at {current_time_str} IST"
      bot.send_message(chat_id=dest_channel, text=message)


# Command to start the bot
def start(update: Update, context: CallbackContext):
  update.message.reply_text("Bot is running.")


# Set up the Telegram bot and handlers
def main():
  updater = Updater(token=TOKEN, use_context=True)
  dispatcher = updater.dispatcher

  # Command to start the bot
  dispatcher.add_handler(CommandHandler("start", start))

  # Command to add main and destination channels with a schedule time
  dispatcher.add_handler(
      CommandHandler("addchannels", add_channels, pass_args=True))

  # Start the bot
  updater.start_polling()

  # Schedule messages to be sent at a specific time in IST
  schedule.every().minute.at(":00").do(send_scheduled_messages)
  schedule.every().minute.at(":30").do(send_scheduled_messages)

  while True:
    schedule.run_pending()
    time.sleep(1)


if __name__ == "__main__":
  main()
