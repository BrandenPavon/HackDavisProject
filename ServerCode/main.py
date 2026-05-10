import os
import uuid
import json
import socket
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

UDP_HOST = os.getenv("UDP_HOST", "0.0.0.0")
UDP_PORT = int(os.getenv("UDP_PORT", "5005"))

client = MongoClient(mongo_uri)
db = client[mongo_db_name]

flex_data = db["hackdavis"]

exercise_states = {
    "active_session_id": None,
    "sessions": {}
}

# O(1) pointer to the current active session in memory.
current_active_session = None
current_active_session_id = None

state_lock = threading.RLock()

_udp_thread_started = False
_udp_thread_lock = threading.Lock()


def utc_now():
    return datetime.now(timezone.utc)


def utc_now_iso():
    return utc_now().isoformat()


def serialize_doc(doc):
    doc["_id"] = str(doc["_id"])

    created_at = doc.get("created_at")
    if isinstance(created_at, datetime):
        doc["created_at"] = created_at.isoformat()

    saved_at = doc.get("saved_at")
    if isinstance(saved_at, datetime):
        doc["saved_at"] = saved_at.isoformat()

    return doc


def get_active_session_state():
    with state_lock:
        if not current_active_session:
            return None

        if not current_active_session.get("start"):
            return None

        return {
            "session_id": current_active_session_id,
            "start": current_active_session.get("start"),
            "started_at": current_active_session.get("started_at"),
            "stopped_at": current_active_session.get("stopped_at"),
            "local_batch_count": len(current_active_session.get("batches", []))
        }


def create_new_session(custom_session_id=None):
    global current_active_session
    global current_active_session_id

    with state_lock:
        now = utc_now_iso()

        old_active_session_id = exercise_states.get("active_session_id")

        if old_active_session_id:
            old_state = exercise_states["sessions"].get(old_active_session_id)

            if old_state and old_state.get("start"):
                old_state["start"] = False
                old_state["stopped_at"] = now

        session_id = custom_session_id or f"session_{uuid.uuid4().hex[:8]}"

        session_state = {
            "session_id": session_id,
            "start": True,
            "started_at": now,
            "stopped_at": None,
            "saved_to_db": False,
            "saved_count": 0,
            "batches": []
        }

        exercise_states["active_session_id"] = session_id
        exercise_states["sessions"][session_id] = session_state

        current_active_session_id = session_id
        current_active_session = session_state

        return {
            "session_id": session_id,
            "start": True,
            "started_at": now,
            "stopped_at": None,
            "local_batch_count": 0
        }


def stop_session(session_id=None):
    global current_active_session
    global current_active_session_id

    with state_lock:
        target_session_id = session_id or exercise_states.get("active_session_id")

        if not target_session_id:
            return None, "No active exercise to stop"

        if target_session_id not in exercise_states["sessions"]:
            return None, "Unknown session_id"

        session_state = exercise_states["sessions"][target_session_id]

        stopped_at = utc_now_iso()

        session_state["start"] = False
        session_state["stopped_at"] = stopped_at

        if exercise_states.get("active_session_id") == target_session_id:
            exercise_states["active_session_id"] = None
            current_active_session_id = None
            current_active_session = None

        batches_ref = session_state.get("batches", [])

        return {
            "session_id": target_session_id,
            "start": False,
            "stopped_at": stopped_at,
            "local_batch_count": len(batches_ref),
            "batches": batches_ref
        }, None


def save_session_batches_to_database(session_id):
    """
    Save all locally buffered batches for a stopped session to MongoDB.
    This is called after /stop_exercise.
    """

    with state_lock:
        session_state = exercise_states["sessions"].get(session_id)

        if not session_state:
            return {
                "saved_count": 0,
                "already_saved": False,
                "message": "Unknown session_id"
            }

        if session_state.get("saved_to_db"):
            return {
                "saved_count": 0,
                "already_saved": True,
                "message": "Session already saved to database"
            }

        batches = list(session_state.get("batches", []))

    if not batches:
        with state_lock:
            if session_id in exercise_states["sessions"]:
                exercise_states["sessions"][session_id]["saved_to_db"] = True

        return {
            "saved_count": 0,
            "already_saved": False,
            "message": "No local batches to save"
        }

    saved_at = utc_now()

    documents = []

    for batch in batches:
        document = dict(batch)
        document["saved_at"] = saved_at
        documents.append(document)

    result = flex_data.insert_many(documents)

    with state_lock:
        if session_id in exercise_states["sessions"]:
            exercise_states["sessions"][session_id]["saved_to_db"] = True
            exercise_states["sessions"][session_id]["saved_count"] = len(result.inserted_ids)

    return {
        "saved_count": len(result.inserted_ids),
        "already_saved": False,
        "message": "Session batches saved to database"
    }


def buffer_flex_batch(body):
    """
    Stores incoming flex sensor batch in local memory only.

    Expected ESP32 UDP JSON format:

    {
        "session_id": "session_abc123",
        "batch_start_ms": 12345,
        "batch_end_ms": 12595,
        "data": [
            [12.3, 45.6, 78.9],
            [12.4, 45.7, 79.0]
        ]
    }
    """

    if not body:
        return None, ("Missing JSON body", 400)

    session_id = body.get("session_id")
    sensor_data = body.get("data")

    if not session_id:
        return None, ("Missing session_id", 400)

    if sensor_data is None:
        return None, ("Missing data", 400)

    if not isinstance(sensor_data, list):
        return None, ("data must be a list", 400)

    for row in sensor_data:
        if not isinstance(row, list):
            return None, ("Each data row must be a list", 400)

        if len(row) != 3:
            return None, ("Each data row must have exactly 3 values", 400)

        if not all(isinstance(value, (int, float)) for value in row):
            return None, ("All flex sensor values must be numbers", 400)

    batch_start_ms = body.get("batch_start_ms")
    batch_end_ms = body.get("batch_end_ms")

    batch_duration_seconds = None
    if isinstance(batch_start_ms, (int, float)) and isinstance(batch_end_ms, (int, float)):
        batch_duration_seconds = max(0, batch_end_ms - batch_start_ms) / 1000.0

    # Store as ISO string so jsonify can dump the active session directly.
    received_at = utc_now_iso()

    batch_document = {
        "session_id": session_id,
        "sensor_type": "flex",
        "batch_start_ms": batch_start_ms,
        "batch_end_ms": batch_end_ms,
        "batch_duration_seconds": batch_duration_seconds,
        "data": sensor_data,
        "created_at": received_at
    }

    with state_lock:
        if not current_active_session:
            return None, ("No active session. Start exercise first.", 404)

        if current_active_session_id != session_id:
            return None, ("Packet session_id does not match active session_id", 409)

        if not current_active_session.get("start"):
            return None, ("Session is not running", 409)

        current_active_session.setdefault("batches", []).append(batch_document)

        local_batch_count = len(current_active_session["batches"])

    return {
        "message": "Flex sensor batch buffered locally",
        "session_id": session_id,
        "local_batch_count": local_batch_count
    }, None


def udp_flex_data_listener():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        sock.bind((UDP_HOST, UDP_PORT))
    except OSError as e:
        print(f"UDP bind failed on {UDP_HOST}:{UDP_PORT}: {e}")
        return

    print(f"UDP flex-data listener running on {UDP_HOST}:{UDP_PORT}")

    while True:
        try:
            packet, address = sock.recvfrom(65535)

            try:
                body = json.loads(packet.decode("utf-8"))
            except json.JSONDecodeError:
                print(f"Invalid JSON from {address}")
                continue

            result, error = buffer_flex_batch(body)

            if error:
                message, status = error
                print(f"UDP flex-data error from {address}: {status} {message}")
                continue

            print(
                f"UDP flex-data buffered from {address}: "
                f"session_id={result['session_id']} "
                f"local_batch_count={result['local_batch_count']}"
            )

        except Exception as e:
            print(f"UDP listener error: {e}")


def start_udp_thread_once():
    global _udp_thread_started

    with _udp_thread_lock:
        if _udp_thread_started:
            return

        udp_thread = threading.Thread(
            target=udp_flex_data_listener,
            daemon=True
        )
        udp_thread.start()

        _udp_thread_started = True
        print("UDP listener thread started")


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
                        "batch_start_ms": document.get("batch_start_ms"),
                        "batch_end_ms": document.get("batch_end_ms"),
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
                "batch_start_ms": batch.get("batch_start_ms"),
                "batch_end_ms": batch.get("batch_end_ms"),
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
        "stopped_at": session["stopped_at"],
        "local_batch_count": session["local_batch_count"]
    }), 200


@app.get("/poll_start_exercise")
def poll_start_exercise():
    session = get_active_session_state()

    if not session:
        return jsonify({
            "start": False,
            "session_id": None,
            "started_at": None,
            "stopped_at": None,
            "local_batch_count": 0
        }), 200

    return jsonify({
        "start": True,
        "session_id": session["session_id"],
        "started_at": session["started_at"],
        "stopped_at": session["stopped_at"],
        "local_batch_count": session["local_batch_count"]
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

    try:
        save_result = save_session_batches_to_database(stopped_session["session_id"])
    except PyMongoError as e:
        return jsonify({
            "error": "Exercise stopped, but failed to save batches to database",
            "details": str(e),
            "session_id": stopped_session["session_id"],
            "local_batch_count": stopped_session["local_batch_count"]
        }), 500

    return jsonify({
        "message": "Exercise stopped and saved to database",
        "session_id": stopped_session["session_id"],
        "start": stopped_session["start"],
        "stopped_at": stopped_session["stopped_at"],
        "local_batch_count": stopped_session["local_batch_count"],
        "database_saved_count": save_result["saved_count"],
        "database_message": save_result["message"]
    }), 200


@app.post("/flex-data")
def post_flex_data():
    """
    Optional HTTP version of flex-data.

    This buffers locally, same as UDP.
    Data is written to MongoDB only after /stop_exercise.
    """

    try:
        body = request.get_json()
        result, error = buffer_flex_batch(body)

        if error:
            message, status = error
            return jsonify({"error": message}), status

        return jsonify(result), 202

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.get("/active-session-data")
def get_active_session_data():
    """
    Incremental in-memory active session endpoint.
    No MongoDB read.

    Client sends:
        /active-session-data?after=123

    Server returns only batches after that index.

    This avoids sending the entire active session every few milliseconds.
    """

    after_raw = request.args.get("after", "-1")

    try:
        after = int(after_raw)
    except ValueError:
        after = -1

    with state_lock:
        if not current_active_session:
            return jsonify({
                "found": False,
                "active": False,
                "message": "No active session in memory",
                "session_id": None,
                "start": False,
                "started_at": None,
                "stopped_at": None,
                "local_batch_count": 0,
                "next_after": -1,
                "batches": []
            }), 200

        batches = current_active_session.get("batches", [])
        total_count = len(batches)

        if after < -1:
            after = -1

        if after >= total_count:
            new_batches = []
        else:
            new_batches = batches[after + 1:]

        return jsonify({
            "found": True,
            "active": True,
            "session_id": current_active_session_id,
            "start": current_active_session.get("start"),
            "started_at": current_active_session.get("started_at"),
            "stopped_at": current_active_session.get("stopped_at"),
            "saved_to_db": current_active_session.get("saved_to_db", False),
            "local_batch_count": total_count,
            "next_after": total_count - 1,
            "new_batch_count": len(new_batches),
            "batches": new_batches
        }), 200


@app.get("/current-exercise-data")
def get_current_exercise_data():
    """
    Returns locally buffered in-memory data for the active or requested session.
    This data may not be in MongoDB yet.
    """

    session_id = request.args.get("session_id")

    with state_lock:
        target_session_id = session_id or exercise_states.get("active_session_id")

        if not target_session_id:
            return jsonify({
                "found": False,
                "message": "No active or requested session found",
                "session_id": None,
                "count": 0,
                "batches": []
            }), 404

        session_state = exercise_states["sessions"].get(target_session_id)

        if not session_state:
            return jsonify({
                "found": False,
                "message": "Unknown session_id",
                "session_id": target_session_id,
                "count": 0,
                "batches": []
            }), 404

        return jsonify({
            "found": True,
            "session_id": target_session_id,
            "start": session_state.get("start"),
            "started_at": session_state.get("started_at"),
            "stopped_at": session_state.get("stopped_at"),
            "saved_to_db": session_state.get("saved_to_db", False),
            "count": len(session_state.get("batches", [])),
            "batches": session_state.get("batches", [])
        }), 200


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
                "message": "No exercise data found in database",
                "session_id": session_id
            }), 404

        created_at = latest_doc.get("created_at")

        if isinstance(created_at, datetime):
            created_at = created_at.isoformat()

        saved_at = latest_doc.get("saved_at")

        if isinstance(saved_at, datetime):
            saved_at = saved_at.isoformat()

        return jsonify({
            "found": True,
            "id": str(latest_doc["_id"]),
            "session_id": latest_doc.get("session_id"),
            "sensor_type": latest_doc.get("sensor_type", "flex"),
            "batch_start_ms": latest_doc.get("batch_start_ms"),
            "batch_end_ms": latest_doc.get("batch_end_ms"),
            "batch_duration_seconds": latest_doc.get("batch_duration_seconds"),
            "data": latest_doc.get("data", []),
            "created_at": created_at,
            "saved_at": saved_at
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
                "message": "No exercise data found in database",
                "session_id": session_id,
                "count": 0,
                "batches": []
            }), 404

        batches = []

        for doc in docs:
            created_at = doc.get("created_at")

            if isinstance(created_at, datetime):
                created_at = created_at.isoformat()

            saved_at = doc.get("saved_at")

            if isinstance(saved_at, datetime):
                saved_at = saved_at.isoformat()

            batches.append({
                "id": str(doc["_id"]),
                "session_id": doc.get("session_id"),
                "sensor_type": doc.get("sensor_type", "flex"),
                "batch_start_ms": doc.get("batch_start_ms"),
                "batch_end_ms": doc.get("batch_end_ms"),
                "batch_duration_seconds": doc.get("batch_duration_seconds"),
                "data": doc.get("data", []),
                "created_at": created_at,
                "saved_at": saved_at
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
            "session_id": None,
            "local_batch_count": 0
        }), 200

    return jsonify({
        "active": True,
        "session_id": session["session_id"],
        "state": {
            "start": session["start"],
            "started_at": session["started_at"],
            "stopped_at": session["stopped_at"],
            "local_batch_count": session["local_batch_count"]
        }
    }), 200


start_udp_thread_once()


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        debug=True,
        port=5000,
        threaded=True,
        use_reloader=False
    )
