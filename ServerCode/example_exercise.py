import time
import random
import requests

BASE_URL = "http://127.0.0.1:5000"
SESSION_ID = "session_001"


def start_exercise():
    url = f"{BASE_URL}/start_exercise"

    payload = {
        "session_id": SESSION_ID
    }

    response = requests.post(url, json=payload)

    print("START")
    print(response.status_code)
    print(response.json())


def send_flex_data(batch_number):
    url = f"{BASE_URL}/flex-data"

    # Simulate one second of flex sensor readings
    # Example: 10 readings per second
    simulated_data = [
        random.randint(450, 700)
        for _ in range(10)
    ]

    payload = {
        "session_id": SESSION_ID,
        "data": simulated_data
    }

    response = requests.post(url, json=payload)

    print(f"BATCH {batch_number}")
    print("Data:", simulated_data)
    print(response.status_code)
    print(response.json())


def stop_exercise():
    url = f"{BASE_URL}/stop_exercise"

    payload = {
        "session_id": SESSION_ID
    }

    response = requests.post(url, json=payload)

    print("STOP")
    print(response.status_code)
    print(response.json())


def main():
    start_exercise()

    #Send 5 seconds of simulated flex data
    for batch_number in range(1, 6):
        send_flex_data(batch_number)
        time.sleep(1)

    stop_exercise()


if __name__ == "__main__":
    main()
