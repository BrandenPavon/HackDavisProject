import os
from collections import OrderedDict
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

class Exercise:
    def __init__(
        self,
        session_id,
        mongo_uri=None,
        mongo_db_name=None,
        collection_name="hackdavis",
    ):
        self.session_id = session_id

        self.mongo_uri = mongo_uri or os.getenv(
            "MONGO_URI",
            "mongodb+srv://bp:bp@cluster0.rywatr7.mongodb.net/?appName=Cluster0"
        )

        self.mongo_db_name = mongo_db_name or os.getenv("MONGO_DB", "hackdavis")

        self.client = MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db_name]
        self.collection = self.db[collection_name]

        self.exercise_data = []

    def begin(self, max_batches=None, timeout_seconds=30):
        """
        Listen for new MongoDB flex sensor batches for this exercise session.

        Returns:
            OrderedDict sorted by created_at timestamp.

        Example return:
        {
            "2026-05-09T12:00:00.123000+00:00": {
                "session_id": "session_123",
                "sensor_type": "flex",
                "data": [512, 518, 521]
            },
            ...
        }
        """

        pipeline = [
            {
                "$match": {
                    "operationType": "insert",
                    "fullDocument.session_id": self.session_id
                }
            }
        ]

        batches_seen = 0

        try:
            with self.collection.watch(
                pipeline,
                full_document="updateLookup",
                max_await_time_ms=1000
            ) as stream:

                start_time = datetime.now(timezone.utc)

                for change in stream:
                    now = datetime.now(timezone.utc)
                    elapsed = (now - start_time).total_seconds()

                    if elapsed >= timeout_seconds:
                        break

                    document = change.get("fullDocument", {})

                    sensor_data = document.get("data", [])
                    created_at = document.get("created_at", now)

                    if not isinstance(sensor_data, list):
                        continue

                    self.exercise_data.append({
                        "session_id": document.get("session_id"),
                        "sensor_type": document.get("sensor_type", "flex"),
                        "batch_duration_seconds": document.get("batch_duration_seconds"),
                        "created_at": created_at,
                        "data": sensor_data,
                    })

                    batches_seen += 1

                    if max_batches is not None and batches_seen >= max_batches:
                        break

        except PyMongoError as e:
            raise RuntimeError(f"MongoDB listen failed: {e}")

        return self.sorted_sensor_data()

    def sorted_sensor_data(self):
        """
        Return all collected exercise sensor batches sorted by timestamp.
        """

        sorted_batches = sorted(
            self.exercise_data,
            key=lambda item: item["created_at"]
        )

        result = OrderedDict()

        for batch in sorted_batches:
            timestamp = batch["created_at"]

            if isinstance(timestamp, datetime):
                timestamp_key = timestamp.isoformat()
            else:
                timestamp_key = str(timestamp)

            result[timestamp_key] = {
                "session_id": batch["session_id"],
                "sensor_type": batch["sensor_type"],
                "batch_duration_seconds": batch["batch_duration_seconds"],
                "data": batch["data"],
            }

        return result

    def summarize(self):
        """
        Basic summary of all sensor values collected so far.
        """

        all_values = []

        for batch in self.exercise_data:
            for value in batch["data"]:
                if isinstance(value, dict):
                    value = value.get("value")

                if isinstance(value, (int, float)):
                    all_values.append(value)

        if not all_values:
            return {
                "session_id": self.session_id,
                "count": 0,
                "min": None,
                "max": None,
                "average": None,
            }

        return {
            "session_id": self.session_id,
            "count": len(all_values),
            "min": min(all_values),
            "max": max(all_values),
            "average": sum(all_values) / len(all_values),
        }

    def close(self):
        self.client.close()


@app.get("/")
def home():
    try:
        data = list(flex_data.find())
        data = [serialize_doc(doc) for doc in data]

        print("MongoDB Data:", data)
        exercise = Exercise(session_id="session_001")

        data = exercise.begin(
            max_batches=5,
            timeout_seconds=30
        )
        summary = exercise.summarize()

        print(data)
        print(summary)

        exercise.close()
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
    app.run(debug=True, port=5000)
