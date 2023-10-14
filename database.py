import pymongo

# Function to initialize a MongoDB connection and create a database
def create_database():
    client = pymongo.MongoClient("mongodb+srv://kagut:kagut@cluster0.hol7gj5.mongodb.net/?retryWrites=true&w=majority:27017")  # Replace with your MongoDB URI
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

# Create the database and collections
db = create_database()

# Example usage
add_channel(db, "@main_channel1", "@dest_channel1", "12:00")
add_channel(db, "@main_channel2", "@dest_channel2", "15:30")

channels = get_channels(db)
for channel in channels:
    print(f"ID: {channel['_id']}, Main: {channel['main_channel']}, Destination: {channel['destination_channel']}, Schedule Time: {channel['schedule_time']}")

# Remove a channel (for example, remove the first channel)
for channel in channels:
    if channel["main_channel"] == "@main_channel1":
        remove_channel(db, channel["_id"])
