import time
import random
import requests

BASE_URL = "http://127.0.0.1:5000"


def get_active_session_id():
    url = f"{BASE_URL}/active-session"

    response = requests.get(url)
    data = response.json()

    print("ACTIVE SESSION")
    print(response.status_code)
    print(data)

    if response.ok and data.get("active") is True:
        return data.get("session_id")

    return None


def send_flex_data(session_id, batch_number):
    url = f"{BASE_URL}/flex-data"

    # Simulate one second of flex sensor readings.
    # Each row is:
    # [flex_sensor_1, flex_sensor_2, flex_sensor_3]
    simulated_data = [
        [
            random.randint(450, 700),
            random.randint(450, 700),
            random.randint(450, 700)
        ]
        for _ in range(10)
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


def main():
    session_id = get_active_session_id()

    if not session_id:
        print("No active session found.")
        print("Start an exercise first from the website or by calling /start_exercise.")
        return

    print("Using active session_id:", session_id)

    # Send 5 seconds of simulated flex data
    for batch_number in range(1, 90):
        send_flex_data(session_id, batch_number)
        time.sleep(0.25)


if __name__ == "__main__":
    main()
