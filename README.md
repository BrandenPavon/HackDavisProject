<div align="center">

<picture>
  <img src="docs/media/img/logo.png" alt="Flex Sensor Exercise Dashboard Logo" width="120" />
</picture>

# Flex Sensor Exercise Dashboard

**Real-time wearable exercise monitoring with ESP32 flex sensors, Flask, Socket.IO, and MongoDB.**

<br>

![Python](https://img.shields.io/badge/Python-3.10+-gray?style=flat&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-Realtime_Server-gray?style=flat&logo=flask&logoColor=white)
![Socket.IO](https://img.shields.io/badge/Socket.IO-Live_Dashboard-gray?style=flat&logo=socketdotio&logoColor=white)
![ESP32](https://img.shields.io/badge/ESP32-Sensor_Client-gray?style=flat&logo=espressif&logoColor=white)
![MongoDB](https://img.shields.io/badge/MongoDB-Session_Storage-gray?style=flat&logo=mongodb&logoColor=white)

</div>

<br>
<br>

<div align="center">
  <picture>
    <img src="docs/media/img/dashboard-preview.png" alt="Flex Sensor Exercise Dashboard Preview" width="900" />
  </picture>
</div>

<br>

<p align="center">
A clinical-style dashboard for tracking patient flex sensor exercises in real time.<br>
Streams flex sensor and wrist angle data, counts repetitions, visualizes movement, and stores completed sessions.
</p>

<br>

> [!NOTE]
> This project is a prototype exercise monitoring system. It is not a medical device and should not be used for diagnosis, treatment decisions, or emergency monitoring.

<br>

<div align="center">

## Features

</div>

<table align="center">
<tr>
<td width="50%" valign="top">

### Real-time monitoring
- **Live session controls** for starting and stopping exercise sessions
- **Socket.IO dashboard updates** for active session state and incoming sensor batches
- **Flex sensor graph** showing live readings for three flex channels
- **2D wrist position view** using `angle_x` and `angle_y` from the incoming data stream
- **Raw response panel** for debugging live packets and connection state

### Exercise analytics
- **Automatic repetition counting** when flex values rise above baseline and return to baseline
- **Per-sensor rep totals** for Flex 1, Flex 2, and Flex 3
- **Combined total reps** across all flex sensors
- **Movement interpretation banner** showing whether the patient is actively flexing
- **Latest wrist angle summary** for quick movement feedback

</td>
<td width="50%" valign="top">

### Backend + data flow
- **Flask API** for session control, polling, and historical session data
- **UDP listener** for incoming ESP32 or sensor gateway packets
- **HTTP `/flex-data` endpoint** for alternate sensor ingestion
- **MongoDB storage** for saved exercise batches
- **Session-specific retrieval** for reviewing completed exercises

### Frontend quality
- **Responsive layout** for desktop and tablet-style displays
- **Clinical-style UI** with cards, metrics, movement rules, and status badges
- **Accessible status text** for connection, session, and movement states
- **Optimized canvas rendering** for smoother live visualization
- **No backend API changes required** for frontend improvements

</td>
</tr>
</table>

<br>

---

<br>

<div align="center">

## Screenshots

<br>

<table>
<tr>
<td align="center">
  <img src="docs/media/img/dashboard-overview.png" alt="Dashboard Overview" width="800" />
<br>
<strong>Dashboard Overview</strong><br>
<em>Current session controls, live metrics, sensor rules, and visualizations</em>
<br><br>
</td>
</tr>
<tr>
<td align="center">
  <img src="docs/media/img/flex-chart.png" alt="Flex Sensor Chart" width="800" />
<br>
<strong>Flex Sensor Chart</strong><br>
<em>Live flex sensor values with baseline reference</em>
<br><br>
</td>
</tr>
<tr>
<td align="center">
  <img src="docs/media/img/wrist-position.png" alt="Wrist Position Visualization" width="500" />
<br>
<strong>2D Wrist Position</strong><br>
<em>Wrist movement mapped from angle_x and angle_y values</em>
<br><br>
</td>
</tr>
</table>

</div>

<br>

---

<br>

<div align="center">

## Technical Implementation

</div>

<table>
<tr>
<td width="50%" valign="top">

**Core architecture**
- ESP32 or sensor client sends batches of flex sensor data
- Flask backend manages active exercise sessions
- UDP listener receives real-time sensor packets
- Socket.IO broadcasts live data to connected browsers
- MongoDB stores completed session batches for later review

</td>
<td width="50%" valign="top">

**Data format**
- Each sensor row uses five values:
  ```json
  [flex1, flex2, flex3, angle_x, angle_y]
  ```
- A full packet contains:
  ```json
  {
    "session_id": "session_123",
    "batch_start_ms": 1000,
    "batch_end_ms": 1100,
    "data": [[15, 16, 14, 2.1, -1.4]]
  }
  ```

</td>
</tr>
</table>

<br>

---

<br>

<div align="center">

## Project Structure

</div>

```text
.
├── main.py                         # Flask, Socket.IO, UDP listener, MongoDB session storage
├── templates/
│   └── index.html                  # Patient dashboard UI
├── esp32-flex-sensor-client/       # ESP32 firmware / sensor sender code
├── docs/
│   └── media/
│       └── img/                    # README images and dashboard screenshots
├── .env                            # Local environment variables, not committed
├── requirements.txt                # Python dependencies
└── README.md
```

<br>

---

<br>

<div align="center">

## Getting Started

</div>

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
cd YOUR_REPO_NAME
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate
```

On Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

Example `requirements.txt`:

```txt
flask
flask-socketio
pymongo
python-dotenv
```

### 4. Configure environment variables

Create a `.env` file:

```env
SECRET_KEY=replace-this-with-a-random-secret
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/?appName=Cluster0
MONGO_DB=hackdavis
UDP_HOST=0.0.0.0
UDP_PORT=5005
```

### 5. Start the Flask server

```bash
python main.py
```

The dashboard runs at:

```text
http://localhost:5000
```

<br>

---

<br>

<div align="center">

## API Reference

</div>

<table>
<tr>
<th>Method</th>
<th>Endpoint</th>
<th>Description</th>
</tr>
<tr>
<td><code>GET</code></td>
<td><code>/</code></td>
<td>Serves the patient dashboard</td>
</tr>
<tr>
<td><code>GET</code></td>
<td><code>/socket-debug</code></td>
<td>Checks Socket.IO server status and UDP configuration</td>
</tr>
<tr>
<td><code>POST</code></td>
<td><code>/start_exercise</code></td>
<td>Starts a new exercise session</td>
</tr>
<tr>
<td><code>POST</code></td>
<td><code>/stop_exercise</code></td>
<td>Stops the active session and saves batches to MongoDB</td>
</tr>
<tr>
<td><code>POST</code></td>
<td><code>/flex-data</code></td>
<td>Accepts a flex sensor batch over HTTP</td>
</tr>
<tr>
<td><code>GET</code></td>
<td><code>/active-session</code></td>
<td>Returns current active session state</td>
</tr>
<tr>
<td><code>GET</code></td>
<td><code>/active-session-data</code></td>
<td>Returns buffered active session batches</td>
</tr>
<tr>
<td><code>GET</code></td>
<td><code>/exercise-data?session_id=...</code></td>
<td>Loads saved session data from MongoDB</td>
</tr>
<tr>
<td><code>GET</code></td>
<td><code>/last-exercise-data</code></td>
<td>Returns the latest saved exercise batch</td>
</tr>
</table>

<br>

---

<br>

<div align="center">

## Socket.IO Events

</div>

<table>
<tr>
<th>Event</th>
<th>Direction</th>
<th>Description</th>
</tr>
<tr>
<td><code>request_active_session</code></td>
<td>Browser → Server</td>
<td>Requests the current session state and recent data</td>
</tr>
<tr>
<td><code>ping_test</code></td>
<td>Browser → Server</td>
<td>Tests the Socket.IO connection</td>
</tr>
<tr>
<td><code>active_session_state</code></td>
<td>Server → Browser</td>
<td>Sends active/inactive session state</td>
</tr>
<tr>
<td><code>active_session_snapshot</code></td>
<td>Server → Browser</td>
<td>Sends recent buffered session batches</td>
</tr>
<tr>
<td><code>session_started</code></td>
<td>Server → Browser</td>
<td>Notifies dashboard that a new session started</td>
</tr>
<tr>
<td><code>flex_batch</code></td>
<td>Server → Browser</td>
<td>Streams a live flex sensor batch to the dashboard</td>
</tr>
<tr>
<td><code>session_stopped</code></td>
<td>Server → Browser</td>
<td>Notifies dashboard that a session stopped and was saved</td>
</tr>
</table>

<br>

---

<br>

<div align="center">

## ESP32 Sensor Packet

</div>

The ESP32 or gateway should send JSON packets using this structure:

```json
{
  "session_id": "session_123",
  "batch_start_ms": 1000,
  "batch_end_ms": 1100,
  "data": [
    [15, 16, 14, 2.1, -1.4],
    [16, 18, 15, 2.4, -1.1],
    [14, 15, 15, 2.0, -0.8]
  ]
}
```

The dashboard expects each row to contain:

```text
[flex1, flex2, flex3, angle_x, angle_y]
```

<br>

---

<br>

<div align="center">

## Movement Logic

</div>

The dashboard uses a default flex baseline of:

```text
15
```

A repetition is counted when:

1. A flex sensor value rises above `15`
2. The same sensor later returns to `15` or below

This creates one return cycle for that sensor.

<br>

---

<br>

<div align="center">

## Recommended Improvements

</div>

<table>
<tr>
<td width="50%" valign="top">

### Hardware + protocol
- Add a `device_id` to each ESP32 packet
- Add a `batch_id` or sequence number to detect duplicates
- Consider MQTT for more reliable IoT transport
- Add calibration mode for patient-specific baselines

</td>
<td width="50%" valign="top">

### Software
- Move secrets out of code and into `.env`
- Add authentication before clinical or public use
- Add automated tests for session and packet validation
- Add CSV export for saved exercise sessions
- Add patient/session metadata fields

</td>
</tr>
</table>

<br>

---

<br>

<div align="center">

## FAQ

</div>

<details>
<summary><b>Does this require MongoDB?</b></summary>
<br>
MongoDB is used for saving completed exercise sessions. The live dashboard can still display active session data while the server is running, but historical loading depends on the database connection.
</details>

<details>
<summary><b>Can the sensor send data over HTTP instead of UDP?</b></summary>
<br>
Yes. The backend includes a <code>POST /flex-data</code> endpoint that accepts the same JSON packet structure used by the UDP listener.
</details>

<details>
<summary><b>What does the wrist position chart show?</b></summary>
<br>
The wrist chart maps <code>angle_x</code> to horizontal movement and <code>angle_y</code> to vertical movement. The center represents a neutral wrist position.
</details>

<details>
<summary><b>How are reps counted?</b></summary>
<br>
Each flex sensor has its own above-baseline state. A rep is counted when the sensor crosses above the baseline and later returns to baseline or below.
</details>

<details>
<summary><b>Is this ready for clinical use?</b></summary>
<br>
No. This is a prototype dashboard and data collection system. Clinical use would require validation, security review, privacy controls, reliability testing, and regulatory review.
</details>

<br>

---

<br>

<div align="center">

### Credits

Built for real-time exercise monitoring using ESP32 sensors, Flask, Socket.IO, MongoDB, and a browser-based dashboard.

<br>

![Issues](https://img.shields.io/badge/Report-Issues-orange?style=flat&logo=github)
![Contributions](https://img.shields.io/badge/Contributions-Welcome-gray?style=flat&logo=github)

<br>

Developed by **Branden Pavon**, **Nicolas Holasek**, ** Serafim Sharkov**, ** Mirzett Evans IV **, **Neil Artista**

</div>
