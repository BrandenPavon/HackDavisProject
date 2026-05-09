import os
from bson import ObjectId
from dotenv import load_dotenv
from flask import Flask, jsonify, request, render_template
from pymongo import MongoClient
from pymongo.errors import PyMongoError

load_dotenv()
app = Flask(__name__)

mongo_uri = os.getenv("MONGO_URI", "mongodb+srv://bp:bp@cluster0.rywatr7.mongodb.net/?appName=Cluster0")
mongo_db_name = os.getenv("MONGO_DB", "sample_mflix")

client = MongoClient(mongo_uri)
db = client[mongo_db_name]
users = db["users"]

# Helper function to convert ObjectId to string
def serialize_user(user):
    user["_id"] = str(user["_id"])
    return user

@app.get("/")
def home():
    try:
        data = list(users.find())  # fetch all documents
        data = [serialize_user(user) for user in data]

        print("MongoDB Data:", data)  # prints to console

        return jsonify(data)  # returns data as JSON in browser
    except PyMongoError as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
