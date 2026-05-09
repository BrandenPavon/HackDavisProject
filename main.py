import os
from datetime import datetime, timezone
from bson import ObjectId
from dotenv import load_dotenv
from flask import Flask, jsonify, request, render_template
from pymongo import MongoClient
from pymongo.errors import PyMongoError

load_dotenv()
app = Flask(__name__)

mongo_uri = os.getenv(
    "MONGO_URI",
    "mongodb+srv://bp:bp@cluster0.rywatr7.mongodb.net/?appName=Cluster0"
)
mongo_db_name = os.getenv("MONGO_DB", "hackdavis")

client = MongoClient(mongo_uri)
db = client[mongo_db_name]

# Collection for flex sensor batches
flex_data = db["hackdavis"]

def serialize_doc(doc):
    doc["_id"] = str(doc["_id"])
    return doc

@app.get("/")
def home():
    try:
        data = list(flex_data.find())
        data = [serialize_doc(doc) for doc in data]

        print("MongoDB Data:", data)

        return jsonify(data)
    except PyMongoError as e:
        return jsonify({"error": str(e)}), 500


@app.post("/flex-data")
def post_flex_data():
    """
    Expected JSON format:

    {
        "session_id": "session_123",
        "data": [512, 518, 521, 519, 530]
    }

    Optional:
    {
        "session_id": "session_123",
        "data": [
            {"timestamp": 0.0, "value": 512},
            {"timestamp": 0.1, "value": 518}
        ]
    }
    """

    try:
        body = request.get_json()

        if not body:
            return jsonify({"error": "Missing JSON body"}), 400

        session_id = body.get("session_id")
        sensor_data = body.get("data")

        if not session_id:
            return jsonify({"error": "Missing session_id"}), 400

        if sensor_data is None:
            return jsonify({"error": "Missing data"}), 400

        if not isinstance(sensor_data, list):
            return jsonify({"error": "data must be a list"}), 400

        document = {
            "session_id": session_id,
            "sensor_type": "flex",
            "batch_duration_seconds": 1,
            "data": sensor_data,
            "created_at": datetime.now(timezone.utc)
        }

        result = flex_data.insert_one(document)

        return jsonify({
            "message": "Flex sensor batch saved successfully",
            "id": str(result.inserted_id),
            "session_id": session_id
        }), 201

    except PyMongoError as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.get("/flex-data/<session_id>")
def get_flex_data_by_session(session_id):
    try:
        data = list(flex_data.find({"session_id": session_id}))
        data = [serialize_doc(doc) for doc in data]

        return jsonify(data), 200

    except PyMongoError as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
