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

# Function to initialize a MongoDB connection and create a database
def create_database():
    client = pymongo.MongoClient("mongodb+srv://kagut:kagut@cluster0.hol7gj5.mongodb.net/?retryWrites=true&w=majority:27017")  # Replace with your MongoDB URI
    db = client["channel_scheduler"]
    return db

import pymongo
from telegram import Bot, Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Your Telegram bot token
TOKEN = "YOUR_BOT_TOKEN"

# Function to initialize a MongoDB connection and create a database
def create_database():
    client = pymongo.MongoClient("mongodb://localhost:27017")  # Replace with your MongoDB URI
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

# Function to remove a channel from the database
def remove_channel(db, channel_id):
    channels = db["channels"]
    channels.delete_one({"_id": channel_id})

# Function to list added channels
def list_channels(update: Update, context: CallbackContext, db):
    channels = get_channels(db)
    channel_list = ["Channels in the database:"]
    for channel in channels:
        channel_list.append(f"Main: {channel['main_channel']}, Destination: {channel['destination_channel']}, Schedule Time: {channel['schedule_time']}")
    update.message.reply_text("\n".join(channel_list))

# Function to forward messages from the main channel to the destination channel
def forward_messages(update: Update, context: CallbackContext, db):
    channels = get_channels(db)

    for channel in channels:
        main_channel = channel['main_channel']
        destination_channel = channel['destination_channel']
        if update.message.chat_id == main_channel:
            context.bot.forward_message(chat_id=destination_channel, from_chat_id=main_channel, message_id=update.message.message_id)

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

# Command to remove a channel by specifying its main and destination channels
def remove_channel_command(update: Update, context: CallbackContext):
    if len(context.args) != 2:
        update.message.reply_text("Usage: /removechannel main_channel_id destination_channel_id")
        return

    main_channel = int(context.args[0])
    destination_channel = int(context.args[1])

    db = create_database()
    channels = get_channels(db)

    for channel in channels:
        if channel['main_channel'] == main_channel and channel['destination_channel'] == destination_channel:
            remove_channel(db, channel['_id'])
            update.message.reply_text("Channel removed from the database.")
            return

    update.message.reply_text("Channel not found in the database.")

# Function to start the bot
def start(update: Update, context: CallbackContext):
    update.message.reply_text("Bot is running. Use /addchannel, /removechannel, or /listchannels to manage channels.")

# Main function to run the bot
def main():
    db = create_database()

    updater = Updater(token=TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("addchannel", add_channel_command, pass_args=True))
    dispatcher.add_handler(CommandHandler("removechannel", remove_channel_command, pass_args=True))
    dispatcher.add_handler(CommandHandler("listchannels", list_channels, pass_args=False, pass_user_data=False))
    dispatcher.add_handler(MessageHandler(Filters.text & Filters.chat_type.channel, forward_messages, pass_chat_data=True, pass_user_data=False))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
