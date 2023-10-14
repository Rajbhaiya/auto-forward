import schedule
import logging
import asyncio
import time
from pyrogram import Client, filters
from datetime import datetime
import pymongo
from telegram import Bot, Update
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackContext

# Your Telegram bot token
TOKEN = "6680969743:AAHpx2FWxrJDDBZTasyyUk05h7a0zG6aeMc"
DB_URI = "mongodb+srv://kagut:kagut@cluster0.hol7gj5.mongodb.net/?retryWrites=true&w=majority"
PORT = 27017

# Function to initialize a MongoDB connection and create a database
def create_database():
    client = pymongo.MongoClient(DB_URI, PORT)  # Replace with your MongoDB URI
    db = client["channel_scheduler"]
    return db

# Function to add a channel to the database
def add_channel(db, main_channel, destination_channel, schedule_time):
    channels = db["channels"]
    channel_data = {
        "main_channel": main_channel,
        "destination_channel": destination_channel,
        "schedule_time": schedule_time
    }
    channels.insert_one(channel_data)

# Function to retrieve all channel information from the database
def get_channels(db):
    channels = db["channels"]
    return channels.find()

# Function to forward messages from the main channel to the destination channel
def forward_messages(context):
    db = create_database()
    channels = get_channels(db)

    current_time = datetime.now(pytz.timezone("Asia/Kolkata"))
    current_time_str = current_time.strftime("%H:%M")

    for channel in channels:
        main_channel = channel['main_channel']
        destination_channel = channel['destination_channel']
        schedule_time = channel['schedule_time']

        if current_time_str == schedule_time:
            context.bot.forward_message(chat_id=destination_channel, from_chat_id=main_channel, message_id=context.job.context.message_id)

# Command to add a channel with main and destination channels as integers and a schedule time
def add_channel_command(update: Update, context: CallbackContext):
    if len(context.args) != 3:
        update.message.reply_text("Usage: /addchannel main_channel_id destination_channel_id HH:MM")
        return

    main_channel = int(context.args[0])
    destination_channel = int(context.args[1])
    schedule_time = context.args[2]

    db = create_database()
    add_channel(db, main_channel, destination_channel, schedule_time)
    update.message.reply_text("Channel added to the database.")

# Function to start the bot
def start(update: Update, context: CallbackContext):
    update.message.reply_text("Bot is running. Use /addchannel to add channels with schedule times.")

# Main function to run the bot
def main():
    db = create_database()

    updater = Updater(token=TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("addchannel", add_channel_command, pass_args=True))

    updater.start_polling()

    # Schedule messages to be forwarded according to the schedule
    schedule.every().minute.at(":00").do(forward_messages, context=updater.bot)
    schedule.every().minute.at(":30").do(forward_messages, context=updater.bot)

    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()
