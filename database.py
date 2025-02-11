from pymongo import MongoClient
from pymongo.server_api import ServerApi

# MongoDB connection URI
uri = "mongodb+srv://210130107014:kkkresha@cluster0.tamsc.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
port = 8000 

# Create a new client and connect to the server
client = MongoClient(uri, port, server_api=ServerApi('1'))
db = client.Blogging  # Connect to the "Blogging" database
users_collection = db["users"]  # Connect to the "users" collection

# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)