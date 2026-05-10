#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <WiFiUdp.h>

WiFiUDP udp;

const char* udpHost = "192.168.137.154";
const int udpPort = 5005;

const char* ssid = "FOURSCOMP 6563";
const char* password = "electric";

const char* pollStartURL = "http://192.168.137.154:5000/poll_start_exercise";

String sessionID = "";

const int flexPins[3] = {4, 5, 6};

const unsigned long sampleIntervalMs = 25;
const unsigned long pollIntervalMs = 500;
const int batchSize = 4;

unsigned long lastSampleMs = 0;
unsigned long lastPollMs = 0;
unsigned long lastReconnectAttemptMs = 0;

String state = "idle";

const int rawMin = 1100;
const int rawMax = 2650;

const float alpha = 0.40;

float filteredRaw[3] = {0, 0, 0};
bool filterInitialized[3] = {false, false, false};

float baselineRaw[3] = {0, 0, 0};
bool calibrated = false;

const int calibrationSamples = 20;
int calibrationCount = 0;
float calibrationSum[3] = {0, 0, 0};

float flexBatch[batchSize][3];
int batchCounter = 0;

unsigned long batchStartMs = 0;
unsigned long batchEndMs = 0;

void setup() {
  Serial.begin(115200);

  analogReadResolution(12);
  analogSetAttenuation(ADC_11db);

  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");

  unsigned long startAttempt = millis();

  while (WiFi.status() != WL_CONNECTED && millis() - startAttempt < 5000) {
    delay(250);
    Serial.print(".");
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nConnected!");
    Serial.print("ESP32 IP: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\nWiFi not connected yet. Continuing anyway.");
  }
}

void loop() {
  unsigned long now = millis();

  maintainWiFi(now);

  if (state != "running" && state != "calibrating" && now - lastPollMs >= pollIntervalMs) {
    lastPollMs = now;
    pollStartExercise();
  }

  if (now - lastSampleMs >= sampleIntervalMs) {
    lastSampleMs += sampleIntervalMs;
    sampleSensors();
  }
}

void sampleSensors() {
  float bendPercents[3];

  for (int i = 0; i < 3; i++) {
    int raw = analogRead(flexPins[i]);

    if (!filterInitialized[i]) {
      filteredRaw[i] = raw;
      filterInitialized[i] = true;
    } else {
      filteredRaw[i] = alpha * raw + (1.0 - alpha) * filteredRaw[i];
    }

    bendPercents[i] = calculateBendPercent(i);
  }

  if (state == "calibrating") {
    updateCalibration();
    return;
  }

  if (state == "running" && calibrated) {
    if (batchCounter == 0) {
      batchStartMs = millis();
    }

    for (int i = 0; i < 3; i++) {
      flexBatch[batchCounter][i] = bendPercents[i];
    }

    batchCounter++;

    if (batchCounter >= batchSize) {
      batchEndMs = millis();
      sendBatchUDP();
      batchCounter = 0;
    }
  }
}

float calculateBendPercent(int sensorIndex) {
  if (!calibrated) {
    return 0;
  }

  float denominator = baselineRaw[sensorIndex] - rawMin;

  if (denominator <= 0) {
    return 0;
  }

  float bendAmount = baselineRaw[sensorIndex] - filteredRaw[sensorIndex];
  float bendPercent = bendAmount * 100.0 / denominator;

  return constrain(bendPercent, 0, 100);
}

void pollStartExercise() {
  if (WiFi.status() != WL_CONNECTED) {
    return;
  }

  HTTPClient http;

  String url = String(pollStartURL) + "?session_id=session_001";
  http.begin(url);
  http.setTimeout(75);

  int code = http.GET();

  if (code == 200) {
    String response = http.getString();

    DynamicJsonDocument doc(256);
    DeserializationError error = deserializeJson(doc, response);

    if (!error) {
      bool start = doc["start"];

      if (doc["session_id"]) {
        sessionID = doc["session_id"].as<String>();
      }

      handleExerciseState(start);
    }
  }

  http.end();
}

void handleExerciseState(bool start) {
  if (start && sessionID != "") {
    if (state == "idle") {
      Serial.println("Exercise start received. Starting non-blocking calibration.");

      batchCounter = 0;
      calibrated = false;
      beginCalibration();
    }
  } else {
    if (state != "idle") {
      Serial.println("Exercise stopped.");
    }

    state = "idle";
    calibrated = false;
    batchCounter = 0;
  }
}

void beginCalibration() {
  state = "calibrating";
  calibrationCount = 0;

  for (int i = 0; i < 3; i++) {
    calibrationSum[i] = 0;
  }
}

void updateCalibration() {
  for (int i = 0; i < 3; i++) {
    calibrationSum[i] += filteredRaw[i];
  }

  calibrationCount++;

  if (calibrationCount >= calibrationSamples) {
    for (int i = 0; i < 3; i++) {
      baselineRaw[i] = calibrationSum[i] / calibrationSamples;
      filteredRaw[i] = baselineRaw[i];
      filterInitialized[i] = true;
    }

    calibrated = true;
    state = "running";
    batchCounter = 0;

    Serial.print("Baseline calibrated: ");
    Serial.print(baselineRaw[0]);
    Serial.print(", ");
    Serial.print(baselineRaw[1]);
    Serial.print(", ");
    Serial.println(baselineRaw[2]);
  }
}

void sendBatchUDP() {
  if (WiFi.status() != WL_CONNECTED) {
    return;
  }

  if (sessionID == "") {
    return;
  }

  String json = buildJsonPayload();

  udp.beginPacket(udpHost, udpPort);
  udp.print(json);
  udp.endPacket();
}

String buildJsonPayload() {
  String json = "{";
  json += "\"session_id\":\"" + sessionID + "\",";
  json += "\"batch_start_ms\":" + String(batchStartMs) + ",";
  json += "\"batch_end_ms\":" + String(batchEndMs) + ",";
  json += "\"data\":[";

  for (int i = 0; i < batchSize; i++) {
    json += "[";
    json += String(flexBatch[i][0], 1) + ",";
    json += String(flexBatch[i][1], 1) + ",";
    json += String(flexBatch[i][2], 1);
    json += "]";

    if (i < batchSize - 1) {
      json += ",";
    }
  }

  json += "]}";
  return json;
}

void maintainWiFi(unsigned long now) {
  if (WiFi.status() == WL_CONNECTED) {
    return;
  }

  if (now - lastReconnectAttemptMs < 3000) {
    return;
  }

  lastReconnectAttemptMs = now;

  Serial.println("WiFi disconnected. Reconnect attempt started.");
  WiFi.disconnect();
  WiFi.begin(ssid, password);
}