#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

const char* ssid = "FOURSCOMP 6563";
const char* password = "electric";

// UPDATED endpoint
const char* dataURL = "http://192.168.137.154:5000/flex-data";
const char* pollStartURL = "http://192.168.137.154:5000/poll_start_exercise";

const char* sessionID = "session_001";

const int FLEX_PIN = 4;

int flexMin = 0;
int flexMax = 4095;

String state = "idle";

unsigned long lastCommandTime = 0;

// Buffer for batching
int buffer[5];
int bufferIndex = 0;

void setup() {
  Serial.begin(9600);
  delay(1000);

  analogReadResolution(12);
  analogSetPinAttenuation(FLEX_PIN, ADC_11db);

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
  int raw = analogRead(FLEX_PIN);
  float voltage = raw * (3.3 / 4095.0);

  int bendPercent = map(raw, flexMin, flexMax, 0, 100);
  bendPercent = constrain(bendPercent, 0, 100);

  Serial.print("Raw: ");
  Serial.print(raw);
  Serial.print(" | Voltage: ");
  Serial.print(voltage, 3);
  Serial.print(" V | Bend: ");
  Serial.print(bendPercent);
  Serial.print("% | State: ");
  Serial.println(state);

  // Poll Flask every 1 second
  if (millis() - lastCommandTime >= 1000) {
    pollStartExercise();
    lastCommandTime = millis();
  }

  // Collect data only when running
  if (state == "running") {
    buffer[bufferIndex] = raw;
    bufferIndex++;

    // When buffer fills, send batch
    if (bufferIndex >= 5) {
      sendBatch();
      bufferIndex = 0;
    }
  }

  delay(100);
}

void pollStartExercise() {
  if (WiFi.status() != WL_CONNECTED) return;

  HTTPClient http;

  String url = String(pollStartURL) + "?session_id=" + String(sessionID);
  http.begin(url);

  int code = http.GET();

  Serial.print("Poll code: ");
  Serial.println(code);

  if (code == 200) {
    String response = http.getString();

    Serial.print("Poll response: ");
    Serial.println(response);

    DynamicJsonDocument doc(256);
    DeserializationError error = deserializeJson(doc, response);

    if (error) {
      Serial.println("JSON parse failed");
      http.end();
      return;
    }

    bool start = doc["start"];

    if (start) {
      state = "running";
    } else {
      state = "idle";
    }
  }

  http.end();
}

void sendBatch() {
  if (WiFi.status() != WL_CONNECTED) return;

  HTTPClient http;
  http.begin(dataURL);
  http.addHeader("Content-Type", "application/json");

  String json = "{";
  json += "\"session_id\":\"" + String(sessionID) + "\",";
  json += "\"data\":[";

  for (int i = 0; i < 5; i++) {
    json += String(buffer[i]);
    if (i < 4) json += ",";
  }

  json += "]}";

  int code = http.POST(json);

  Serial.print("POST code: ");
  Serial.println(code);
  Serial.println(http.getString());

  http.end();
}

void calibrateSensor() {
  Serial.println("Calibrating... keep sensor straight.");

  flexMin = analogRead(FLEX_PIN);
  delay(1000);

  Serial.print("New flexMin: ");
  Serial.println(flexMin);
}