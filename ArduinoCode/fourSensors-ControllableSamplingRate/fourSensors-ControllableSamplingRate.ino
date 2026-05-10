#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <WiFiUdp.h>

WiFiUDP udp;

const char* udpHost = "192.168.137.154";
const int udpPort = 5005;

unsigned long batchStartMs = 0;
unsigned long batchEndMs = 0;

const char* ssid = "FOURSCOMP 6563";
const char* password = "electric";

const char* dataURL = "http://192.168.137.154:5000/flex-data";
const char* pollStartURL = "http://192.168.137.154:5000/poll_start_exercise";

String sessionID = "";

const int flexPins[3] = {4, 5, 6};

const unsigned long sampleIntervalMs = 50;    // 20 Hz
const unsigned long pollIntervalMs = 2000;    // poll every 2 sec
const int batchSize = 5;                      // 250 ms batch

unsigned long lastSampleMs = 0;
unsigned long lastPollMs = 0;

String state = "idle";
String lastState = "idle";

const int rawMin = 1100;
const int rawMax = 2650;

const float alpha = 0.40;

float filteredRaw[3] = {0, 0, 0};
bool filterInitialized[3] = {false, false, false};

float baselineRaw[3] = {0, 0, 0};
bool calibrated = false;
const int calibrationSamples = 20;

float flexBatch[batchSize][3];
int batchCounter = 0;

void setup() {
  Serial.begin(115200);

  analogReadResolution(12);
  analogSetAttenuation(ADC_11db);

  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nConnected!");
  Serial.print("ESP32 IP: ");
  Serial.println(WiFi.localIP());
}

void loop() {
  unsigned long now = millis();

  if (now - lastPollMs >= pollIntervalMs) {
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
    reconnectWiFi();
    return;
  }

  HTTPClient http;

  String url = String(pollStartURL) + "?session_id=session_001";
  http.begin(url);
  http.setTimeout(500);

  unsigned long startMs = millis();
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
    } else {
      Serial.println("JSON parse failed");
    }
  } else {
    Serial.print("Poll failed. Code: ");
    Serial.println(code);
  }

  Serial.print("Poll took ms: ");
  Serial.println(millis() - startMs);

  http.end();
}

void handleExerciseState(bool start) {
  if (start && sessionID != "") {
    if (state != "running") {
      Serial.println("Exercise started");

      state = "running";
      batchCounter = 0;

      if (!calibrated) {
        calibrateBaseline();
      }
    }
  } else {
    if (state != "idle") {
      Serial.println("Exercise stopped");
    }

    state = "idle";
    calibrated = false;
    batchCounter = 0;
  }
}

void calibrateBaseline() {
  Serial.println("Calibrating baseline. Keep sensors still...");

  float sum[3] = {0, 0, 0};

  for (int sample = 0; sample < calibrationSamples; sample++) {
    for (int i = 0; i < 3; i++) {
      sum[i] += analogRead(flexPins[i]);
    }

    delay(50);
  }

  for (int i = 0; i < 3; i++) {
    baselineRaw[i] = sum[i] / calibrationSamples;
    filteredRaw[i] = baselineRaw[i];
    filterInitialized[i] = true;
  }

  calibrated = true;

  Serial.print("Baseline calibrated: ");
  Serial.print(baselineRaw[0]);
  Serial.print(", ");
  Serial.print(baselineRaw[1]);
  Serial.print(", ");
  Serial.println(baselineRaw[2]);
}

void sendBatchUDP() {
  if (WiFi.status() != WL_CONNECTED) {
    reconnectWiFi();
    return;
  }

  if (sessionID == "") return;

  String json = buildJsonPayload();

  udp.beginPacket(udpHost, udpPort);
  udp.print(json);
  udp.endPacket();

  Serial.println("UDP batch sent");
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

void reconnectWiFi() {
  Serial.println("WiFi disconnected. Reconnecting...");

  WiFi.disconnect();
  WiFi.begin(ssid, password);

  unsigned long startAttempt = millis();

  while (WiFi.status() != WL_CONNECTED && millis() - startAttempt < 3000) {
    delay(250);
    Serial.print(".");
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi reconnected");
  } else {
    Serial.println("\nWiFi reconnect failed");
  }
}