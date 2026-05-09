import time
import random
import argparse
import requests

BASE_URL = "http://127.0.0.1:5000"


def start_exercise():
    url = f"{BASE_URL}/start_exercise"

    response = requests.post(url, json={})
    data = response.json()

    print("START")
    print(response.status_code)
    print(data)

    return data.get("session_id")


def poll_start_exercise():
    url = f"{BASE_URL}/poll_start_exercise"

    response = requests.get(url)
    data = response.json()

    print("POLL")
    print(response.status_code)
    print(data)

    if data.get("start") is True:
        return data.get("session_id")

    return None


def create_test_sensor_row():
    flex1 = random.randint(450, 700)
    flex2 = random.randint(450, 700)
    flex3 = random.randint(450, 700)

    imu_x = round(random.uniform(-180.0, 180.0), 2)
    imu_y = round(random.uniform(-180.0, 180.0), 2)
    imu_z = round(random.uniform(-180.0, 180.0), 2)

    imu_gforce_x = round(random.uniform(-2.0, 2.0), 3)
    imu_gforce_y = round(random.uniform(-2.0, 2.0), 3)
    imu_gforce_z = round(random.uniform(0.5, 1.5), 3)

    return [
        flex1,
        flex2,
        flex3,
        imu_x,
        imu_y,
        imu_z,
        imu_gforce_x,
        imu_gforce_y,
        imu_gforce_z
    ]


def send_flex_data(session_id, batch_number, samples_per_batch):
    url = f"{BASE_URL}/flex-data"

    simulated_data = [
        create_test_sensor_row()
        for _ in range(samples_per_batch)
    ]

    payload = {
        "session_id": session_id,
        "data": simulated_data
    }

    response = requests.post(url, json=payload)

    print(f"BATCH {batch_number}")
    print("Session:", session_id)
    print("Data:", simulated_data)
    print(response.status_code)
    print(response.json())


def stop_exercise(session_id=None):
    url = f"{BASE_URL}/stop_exercise"

    payload = {}
    if session_id:
        payload["session_id"] = session_id

    response = requests.post(url, json=payload)

    print("STOP")
    print(response.status_code)
    print(response.json())


def run_full_simulation(batches, samples_per_batch):
    print("Running full exercise simulation...")

    session_id = start_exercise()

    if not session_id:
        print("Failed to start exercise. No session_id returned.")
        return

    print(f"Generated session ID: {session_id}")

    polled_session_id = poll_start_exercise()

    if not polled_session_id:
        print("Poll did not return an active session.")
        return

    if polled_session_id != session_id:
        print("Warning: polled session ID does not match started session ID.")
        print("Started:", session_id)
        print("Polled:", polled_session_id)

    for batch_number in range(1, batches + 1):
        send_flex_data(session_id, batch_number, samples_per_batch)
        time.sleep(1)

    stop_exercise(session_id)

    print("Full simulation complete.")
    print(f"View data at: {BASE_URL}/exercise-data?session_id={session_id}")


def main():
    parser = argparse.ArgumentParser(
        description="Control simulated flex sensor exercise"
    )

    parser.add_argument(
        "--start",
        action="store_true",
        help="Start the exercise and generate a new session ID"
    )

    parser.add_argument(
        "--poll",
        action="store_true",
        help="Poll the server like the ESP32 and print the active session ID"
    )

    parser.add_argument(
        "--stop",
        action="store_true",
        help="Stop the active exercise"
    )

    parser.add_argument(
        "--send-data",
        action="store_true",
        help="Send simulated flex sensor data"
    )

    parser.add_argument(
        "--full",
        action="store_true",
        help="Run full simulation: start, poll, send data, stop"
    )

    parser.add_argument(
        "--batches",
        type=int,
        default=5,
        help="Number of 1-second flex data batches to send"
    )

    parser.add_argument(
        "--samples-per-batch",
        type=int,
        default=10,
        help="Number of sensor samples per 1-second batch"
    )

    parser.add_argument(
        "--session-id",
        type=str,
        default=None,
        help="Optional session ID. If omitted, script polls server for active session."
    )

    args = parser.parse_args()

    if args.full:
        run_full_simulation(args.batches, args.samples_per_batch)
        return

    session_id = args.session_id

    if args.start:
        session_id = start_exercise()

    if args.poll:
        session_id = poll_start_exercise()

    if args.send_data:
        if not session_id:
            session_id = poll_start_exercise()

        if not session_id:
            print("No active session found. Run with --start first.")
            return

        for batch_number in range(1, args.batches + 1):
            send_flex_data(session_id, batch_number, args.samples_per_batch)
            time.sleep(1)

    if args.stop:
        stop_exercise(session_id)

    if not args.start and not args.poll and not args.stop and not args.send_data:
        parser.print_help()


if __name__ == "__main__":
    main()
