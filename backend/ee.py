import time
import math
import requests

BASE_URL = "http://127.0.0.1:5000"

CYCLE_SECONDS = 2.0
ROWS_PER_BATCH = 10
BATCH_DELAY_SECONDS = 0.25

MAX_WRIST_ANGLE = 90.0


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


def parabolic_value(t_seconds, offset=0.0):
    """
    Produces a smooth parabola:
    0 -> 100 -> 0
    """
    phase = ((t_seconds + offset) % CYCLE_SECONDS) / CYCLE_SECONDS
    value = 100 * (1 - ((2 * phase - 1) ** 2))
    return round(max(0, min(100, value)), 2)


def angle_x_left_right(t_seconds):
    """
    Moves the wrist dot horizontally:
    -90 -> +90 -> -90

    -90 = fully left
     0  = center
    +90 = fully right
    """
    phase = (t_seconds % CYCLE_SECONDS) / CYCLE_SECONDS
    angle = MAX_WRIST_ANGLE * math.sin(2 * math.pi * phase)
    return round(angle, 2)


def send_flex_data(session_id, batch_number, start_time):
    url = f"{BASE_URL}/flex-data"

    batch_start_ms = int(time.time() * 1000)

    simulated_data = []

    for row_index in range(ROWS_PER_BATCH):
        elapsed = time.time() - start_time

        # Spread rows slightly across the batch so they are not identical.
        t = elapsed + row_index * 0.025

        flex1 = parabolic_value(t, offset=0.0)
        flex2 = parabolic_value(t, offset=0.2)
        flex3 = parabolic_value(t, offset=0.4)

        angle_x = angle_x_left_right(t)
        angle_y = 0.0

        simulated_data.append([
            flex1,
            flex2,
            flex3,
            angle_x,
            angle_y
        ])

    batch_end_ms = int(time.time() * 1000)

    payload = {
        "session_id": session_id,
        "batch_start_ms": batch_start_ms,
        "batch_end_ms": batch_end_ms,
        "data": simulated_data
    }

    response = requests.post(url, json=payload)

    print(f"BATCH {batch_number}")
    print("Session:", session_id)
    print("Data:", simulated_data)
    print(response.status_code)

    try:
        print(response.json())
    except Exception:
        print(response.text)


def main():
    session_id = get_active_session_id()

    if not session_id:
        print("No active session found.")
        print("Start an exercise first from the website or by calling /start_exercise.")
        return

    print("Using active session_id:", session_id)

    start_time = time.time()

    for batch_number in range(1, 90):
        send_flex_data(session_id, batch_number, start_time)
        time.sleep(BATCH_DELAY_SECONDS)


if __name__ == "__main__":
    main()

