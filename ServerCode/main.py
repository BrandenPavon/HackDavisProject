import os
import uuid
import threading
from collections import OrderedDict
from datetime import datetime, timezone

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

# MongoClient is thread-safe.
# Keep one global client and reuse it.
client = MongoClient(mongo_uri)
db = client[mongo_db_name]

# Collection for flex sensor batches.
flex_data = db["hackdavis"]

# In-memory state for the current exercise.
# This is safe for multi-threaded Flask because we protect it with state_lock.
# This is NOT safe for multiple Gunicorn worker processes because each process
# gets its own copy of this dictionary.
exercise_states = {
    "active_session_id": None,
    "sessions": {}
}

state_lock = threading.RLock()


def utc_now():
    return datetime.now(timezone.utc)


def utc_now_iso():
    return utc_now().isoformat()


def serialize_doc(doc):
    doc["_id"] = str(doc["_id"])

    created_at = doc.get("created_at")
    if isinstance(created_at, datetime):
        doc["created_at"] = created_at.isoformat()

    return doc


def get_active_session_state():
    """
    Thread-safe helper.
    Returns a copy of the active session state.
    """

    with state_lock:
        active_session_id = exercise_states.get("active_session_id")

        if not active_session_id:
            return None

        state = exercise_states["sessions"].get(active_session_id)

        if not state or not state.get("start"):
            return None

        return {
            "session_id": active_session_id,
            "start": state.get("start"),
            "started_at": state.get("started_at"),
            "stopped_at": state.get("stopped_at")
        }


def create_new_session(custom_session_id=None):
    """
    Thread-safe helper.
    Creates a new active session.

    If another session is active, mark it stopped first.
    """

    with state_lock:
        now = utc_now_iso()

        old_active_session_id = exercise_states.get("active_session_id")

        if old_active_session_id:
            old_state = exercise_states["sessions"].get(old_active_session_id)

            if old_state and old_state.get("start"):
                old_state["start"] = False
                old_state["stopped_at"] = now

        session_id = custom_session_id or f"session_{uuid.uuid4().hex[:8]}"

        exercise_states["active_session_id"] = session_id
        exercise_states["sessions"][session_id] = {
            "start": True,
            "started_at": now,
            "stopped_at": None
        }

        return {
            "session_id": session_id,
            "start": True,
            "started_at": now,
            "stopped_at": None
        }


def stop_session(session_id=None):
    """
    Thread-safe helper.
    Stops a specific session, or the currently active session if no ID is given.
    """

    with state_lock:
        target_session_id = session_id or exercise_states.get("active_session_id")

        if not target_session_id:
            return None, "No active exercise to stop"

        if target_session_id not in exercise_states["sessions"]:
            return None, "Unknown session_id"

        stopped_at = utc_now_iso()

        exercise_states["sessions"][target_session_id]["start"] = False
        exercise_states["sessions"][target_session_id]["stopped_at"] = stopped_at

        if exercise_states.get("active_session_id") == target_session_id:
            exercise_states["active_session_id"] = None

        return {
            "session_id": target_session_id,
            "start": False,
            "stopped_at": stopped_at
        }, None


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

                start_time = utc_now()

                for change in stream:
                    now = utc_now()
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
        all_values = []

        for batch in self.exercise_data:
            for row in batch["data"]:
                if isinstance(row, list):
                    for value in row:
                        if isinstance(value, (int, float)):
                            all_values.append(value)
                elif isinstance(row, dict):
                    value = row.get("value")
                    if isinstance(value, (int, float)):
                        all_values.append(value)
                elif isinstance(row, (int, float)):
                    all_values.append(row)

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
def go():
    return render_template("index.html")


@app.post("/start_exercise")
def start_exercise():
    body = request.get_json(silent=True) or {}

    custom_session_id = body.get("session_id")

    session = create_new_session(custom_session_id)

    return jsonify({
        "message": "Exercise started",
        "session_id": session["session_id"],
        "start": session["start"],
        "started_at": session["started_at"],
        "stopped_at": session["stopped_at"]
    }), 200


@app.get("/poll_start_exercise")
def poll_start_exercise():
    session = get_active_session_state()

    if not session:
        return jsonify({
            "start": False,
            "session_id": None,
            "started_at": None,
            "stopped_at": None
        }), 200

    return jsonify({
        "start": True,
        "session_id": session["session_id"],
        "started_at": session["started_at"],
        "stopped_at": session["stopped_at"]
    }), 200


@app.post("/stop_exercise")
def stop_exercise():
    body = request.get_json(silent=True) or {}

    requested_session_id = body.get("session_id")

    stopped_session, error = stop_session(requested_session_id)

    if error == "No active exercise to stop":
        return jsonify({
            "error": error
        }), 400

    if error == "Unknown session_id":
        return jsonify({
            "error": error,
            "session_id": requested_session_id
        }), 404

    return jsonify({
        "message": "Exercise stopped",
        "session_id": stopped_session["session_id"],
        "start": stopped_session["start"],
        "stopped_at": stopped_session["stopped_at"]
    }), 200


@app.post("/flex-data")
def post_flex_data():
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

        for row in sensor_data:
            if not isinstance(row, list):
                return jsonify({
                    "error": "Each data row must be a list"
                }), 400

            if len(row) != 3:
                return jsonify({
                    "error": "Each data row must have exactly 3 values",
                    "expected_format": [
                        "flex_sensor_1",
                        "flex_sensor_2",
                        "flex_sensor_3"
                    ]
                }), 400

            if not all(isinstance(value, (int, float)) for value in row):
                return jsonify({
                    "error": "All flex sensor values must be numbers"
                }), 400

        document = {
            "session_id": session_id,
            "sensor_type": "flex",
            "batch_duration_seconds": 1,
            "data": sensor_data,
            "created_at": utc_now()
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


@app.get("/last-exercise-data")
def get_last_exercise_data():
    try:
        session_id = request.args.get("session_id")

        query = {}
        if session_id:
            query["session_id"] = session_id

        latest_doc = flex_data.find_one(
            query,
            sort=[("created_at", -1)]
        )

        if not latest_doc:
            return jsonify({
                "found": False,
                "message": "No exercise data found",
                "session_id": session_id
            }), 404

        created_at = latest_doc.get("created_at")

        if isinstance(created_at, datetime):
            created_at = created_at.isoformat()

        return jsonify({
            "found": True,
            "id": str(latest_doc["_id"]),
            "session_id": latest_doc.get("session_id"),
            "sensor_type": latest_doc.get("sensor_type", "flex"),
            "batch_duration_seconds": latest_doc.get("batch_duration_seconds"),
            "data": latest_doc.get("data", []),
            "created_at": created_at
        }), 200

    except PyMongoError as e:
        return jsonify({"error": str(e)}), 500


@app.get("/exercise-data")
def get_exercise_data():
    try:
        session_id = request.args.get("session_id")

        if not session_id:
            return jsonify({"error": "Missing session_id"}), 400

        docs = list(
            flex_data.find({"session_id": session_id})
            .sort("created_at", 1)
        )

        if not docs:
            return jsonify({
                "found": False,
                "message": "No exercise data found",
                "session_id": session_id,
                "count": 0,
                "batches": []
            }), 404

        batches = []

        for doc in docs:
            created_at = doc.get("created_at")

            if isinstance(created_at, datetime):
                created_at = created_at.isoformat()

            batches.append({
                "id": str(doc["_id"]),
                "session_id": doc.get("session_id"),
                "sensor_type": doc.get("sensor_type", "flex"),
                "batch_duration_seconds": doc.get("batch_duration_seconds"),
                "data": doc.get("data", []),
                "created_at": created_at
            })

        return jsonify({
            "found": True,
            "session_id": session_id,
            "count": len(batches),
            "batches": batches
        }), 200

    except PyMongoError as e:
        return jsonify({"error": str(e)}), 500


@app.get("/flex-data/<session_id>")
def get_flex_data_by_session(session_id):
    try:
        data = list(
            flex_data.find({"session_id": session_id})
            .sort("created_at", 1)
        )

        data = [serialize_doc(doc) for doc in data]

        return jsonify(data), 200

    except PyMongoError as e:
        return jsonify({"error": str(e)}), 500


@app.get("/active-session")
def get_active_session():
    session = get_active_session_state()

    if not session:
        return jsonify({
            "active": False,
            "session_id": None
        }), 200

    return jsonify({
        "active": True,
        "session_id": session["session_id"],
        "state": {
            "start": session["start"],
            "started_at": session["started_at"],
            "stopped_at": session["stopped_at"]
        }
    }), 200


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        debug=True,
        port=5000,
        threaded=True,
        use_reloader=False
    )
