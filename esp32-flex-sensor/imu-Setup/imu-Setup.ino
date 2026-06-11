#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <WiFiUdp.h>
#include <Wire.h>
#include <MPU6050_light.h>

// -------------------- WiFi / UDP --------------------

WiFiUDP udp;

const char* udpHost = "192.168.137.154";
const int udpPort = 5005;

const char* ssid = "FOURSCOMP 6563";
const char* password = "electric";

const char* pollStartURL = "http://192.168.137.154:5000/poll_start_exercise";

String sessionID = "";

// -------------------- MPU6050 --------------------

#define SDA_PIN 8
#define SCL_PIN 9

MPU6050 mpu(Wire);

// 0 = Angle X
// 1 = Angle Y
// 2 = Angle Z, not recommended unless needed
const int wristAxis = 0;

// If extension upward gives negative angle, change this to -1
const int imuDirection = 1;

float neutralAngle = 0.0;
float wristAngle = 0.0;
float smoothedWristAngle = 0.0;

float minAngle = 0.0;
float maxAngle = 0.0;

const float imuAlpha = 0.6;

bool mpuReady = false;

// -------------------- Flex sensors --------------------
//
// Physical layout:
// GPIO 4 = top of hand/wrist, extension sensor 1
// GPIO 5 = top of hand/wrist, extension sensor 2
// GPIO 6 = bottom wrist, flexion sensor

const int flexPins[3] = {4, 5, 6};

const int EXTENSION_TOP_1 = 0;
const int EXTENSION_TOP_2 = 1;
const int FLEXION_BOTTOM  = 2;

// Set these after testing raw values.
// -1 means raw value goes DOWN when bent.
//  1 means raw value goes UP when bent.
const int bendDirection[3] = {
  -1,  // GPIO 4 extension sensor
  -1,  // GPIO 5 extension sensor
  -1   // GPIO 6 flexion sensor
};

const int rawMin = 1100;
const int rawMax = 2650;

const float flexAlpha = 0.40;

float filteredRaw[3] = {0, 0, 0};
bool filterInitialized[3] = {false, false, false};

float baselineRaw[3] = {0, 0, 0};
bool calibrated = false;

// -------------------- Fusion settings --------------------

const float wristDeadzoneDeg = 5.0;

// Adjust these after real testing
const float maxExtensionDeg = 80.0;
const float maxFlexionDeg = 80.0;

// Base fusion weights
const float imuWeight = 0.6;
const float flexWeight = 0.4;

float extensionScore = 0.0;
float flexionScore = 0.0;
float netWristScore = 0.0;
float motionConfidence = 0.0;

float extensionFlexAvg = 0.0;
float extensionFlexDiff = 0.0;
float extensionAgreement = 0.0;

String wristMotion = "neutral";

// -------------------- Timing / state --------------------

const unsigned long sampleIntervalMs = 25;
const unsigned long pollIntervalMs = 500;
const int batchSize = 4;

unsigned long lastSampleMs = 0;
unsigned long lastPollMs = 0;
unsigned long lastReconnectAttemptMs = 0;

String state = "idle";

// -------------------- Calibration --------------------

const int calibrationSamples = 20;
int calibrationCount = 0;

float calibrationSum[3] = {0, 0, 0};
float imuNeutralSum = 0.0;

// -------------------- Batches --------------------

float flexBatch[batchSize][3];

// wristBatch:
// [0] smoothed wrist angle
// [1] raw wrist angle
// [2] min angle
// [3] max angle
// [4] ROM
float wristBatch[batchSize][5];

float fusionBatch[batchSize][6];
// [0] extensionScore
// [1] flexionScore
// [2] netWristScore
// [3] motionConfidence
// [4] extensionFlexAvg
// [5] extensionAgreement

float angleBatch[batchSize][3];
float gyroBatch[batchSize][3];
float accBatch[batchSize][3];
float tempBatch[batchSize];

String motionBatch[batchSize];

int batchCounter = 0;

unsigned long batchStartMs = 0;
unsigned long batchEndMs = 0;

// -------------------- Setup --------------------

void setup() {
  Serial.begin(115200);
  delay(1000);

  analogReadResolution(12);
  analogSetAttenuation(ADC_11db);

  setupMPU();
  setupWiFi();
}

void setupMPU() {
  Wire.begin(SDA_PIN, SCL_PIN);

  byte status = mpu.begin();

  if (status != 0) {
    Serial.print("MPU6050 init failed. Status: ");
    Serial.println(status);
    mpuReady = false;
    return;
  }

  Serial.println("MPU6050 ready.");
  Serial.println("Keep sensor still. Warming up...");
  delay(3000);

  Serial.println("Calculating MPU offsets. Keep still...");
  mpu.calcOffsets(true, true);

  for (int i = 0; i < 100; i++) {
    mpu.update();
    delay(10);
  }

  mpuReady = true;
  Serial.println("MPU offsets calculated.");
}

void setupWiFi() {
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

// -------------------- Main loop --------------------

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

// -------------------- Sensor sampling --------------------

void sampleSensors() {
  if (mpuReady) {
    mpu.update();
  }

  float bendPercents[3];

  for (int i = 0; i < 3; i++) {
    int raw = analogRead(flexPins[i]);

    if (!filterInitialized[i]) {
      filteredRaw[i] = raw;
      filterInitialized[i] = true;
    } else {
      filteredRaw[i] = flexAlpha * raw + (1.0 - flexAlpha) * filteredRaw[i];
    }

    bendPercents[i] = calculateBendPercent(i);
  }

  if (state == "calibrating") {
    updateCalibration();
    return;
  }

  if (state == "running" && calibrated && mpuReady) {
    updateWristAngle();

    // This is the main fusion step
    updateFusedWristMetrics(bendPercents);

    if (batchCounter == 0) {
      batchStartMs = millis();
    }

    saveBatchSample(bendPercents);

    batchCounter++;

    if (batchCounter >= batchSize) {
      batchEndMs = millis();
      sendBatchUDP();
      batchCounter = 0;
    }
  }
}

// -------------------- IMU wrist angle --------------------

void updateWristAngle() {
  float currentAngle = getSelectedIMUAngle();

  wristAngle = currentAngle - neutralAngle;

  smoothedWristAngle = imuAlpha * wristAngle + (1.0 - imuAlpha) * smoothedWristAngle;

  if (smoothedWristAngle < minAngle) {
    minAngle = smoothedWristAngle;
  }

  if (smoothedWristAngle > maxAngle) {
    maxAngle = smoothedWristAngle;
  }
}

float getSelectedIMUAngle() {
  if (wristAxis == 0) {
    return mpu.getAngleX();
  } else if (wristAxis == 1) {
    return mpu.getAngleY();
  } else {
    return mpu.getAngleZ();
  }
}

// -------------------- Flex calculation --------------------

float calculateBendPercent(int sensorIndex) {
  if (!calibrated) {
    return 0;
  }

  float bendAmount;

  if (bendDirection[sensorIndex] == -1) {
    bendAmount = baselineRaw[sensorIndex] - filteredRaw[sensorIndex];
  } else {
    bendAmount = filteredRaw[sensorIndex] - baselineRaw[sensorIndex];
  }

  float bendPercent = bendAmount * 100.0 / abs(rawMax - rawMin);

  return constrain(bendPercent, 0, 100);
}

// -------------------- Sensor fusion --------------------

void updateFusedWristMetrics(float bendPercents[3]) {
  float correctedAngle = imuDirection * smoothedWristAngle;

  // GPIO 4 and GPIO 5 both measure extension
  extensionFlexAvg =
    (bendPercents[EXTENSION_TOP_1] + bendPercents[EXTENSION_TOP_2]) / 2.0;

  extensionFlexDiff =
    abs(bendPercents[EXTENSION_TOP_1] - bendPercents[EXTENSION_TOP_2]);

  // High agreement means extension sensors are similar
  extensionAgreement = 100.0 - extensionFlexDiff;
  extensionAgreement = constrain(extensionAgreement, 0, 100);

  // GPIO 6 measures flexion
  float flexionFlexPercent = bendPercents[FLEXION_BOTTOM];

  float imuExtensionPercent = 0.0;
  float imuFlexionPercent = 0.0;

  if (correctedAngle > wristDeadzoneDeg) {
    imuExtensionPercent = correctedAngle * 100.0 / maxExtensionDeg;
  } else if (correctedAngle < -wristDeadzoneDeg) {
    imuFlexionPercent = (-correctedAngle) * 100.0 / maxFlexionDeg;
  }

  imuExtensionPercent = constrain(imuExtensionPercent, 0, 100);
  imuFlexionPercent = constrain(imuFlexionPercent, 0, 100);

  // If sensors 4 and 5 disagree, trust extension flex sensors less
  float adjustedExtensionFlexWeight = flexWeight * (extensionAgreement / 100.0);
  float adjustedExtensionImuWeight = 1.0 - adjustedExtensionFlexWeight;

  extensionScore =
    adjustedExtensionImuWeight * imuExtensionPercent +
    adjustedExtensionFlexWeight * extensionFlexAvg;

  // Flexion only has one flex sensor, so use base weights
  flexionScore =
    imuWeight * imuFlexionPercent +
    flexWeight * flexionFlexPercent;

  extensionScore = constrain(extensionScore, 0, 100);
  flexionScore = constrain(flexionScore, 0, 100);

  netWristScore = extensionScore - flexionScore;

  if (abs(correctedAngle) < wristDeadzoneDeg && extensionScore < 10 && flexionScore < 10) {
    wristMotion = "neutral";
  } else if (extensionScore > flexionScore) {
    wristMotion = "extension";
  } else {
    wristMotion = "flexion";
  }

  float scoreDifference = abs(extensionScore - flexionScore);

  // Confidence combines:
  // 1. how strongly extension/flexion wins
  // 2. whether sensors 4 and 5 agree
  motionConfidence = 0.7 * scoreDifference + 0.3 * extensionAgreement;
  motionConfidence = constrain(motionConfidence, 0, 100);
}

// -------------------- Batch save --------------------

void saveBatchSample(float bendPercents[3]) {
  for (int i = 0; i < 3; i++) {
    flexBatch[batchCounter][i] = bendPercents[i];
  }

  float totalRange = maxAngle - minAngle;

  wristBatch[batchCounter][0] = smoothedWristAngle;
  wristBatch[batchCounter][1] = wristAngle;
  wristBatch[batchCounter][2] = minAngle;
  wristBatch[batchCounter][3] = maxAngle;
  wristBatch[batchCounter][4] = totalRange;

  fusionBatch[batchCounter][0] = extensionScore;
  fusionBatch[batchCounter][1] = flexionScore;
  fusionBatch[batchCounter][2] = netWristScore;
  fusionBatch[batchCounter][3] = motionConfidence;
  fusionBatch[batchCounter][4] = extensionFlexAvg;
  fusionBatch[batchCounter][5] = extensionAgreement;

  motionBatch[batchCounter] = wristMotion;

  angleBatch[batchCounter][0] = mpu.getAngleX();
  angleBatch[batchCounter][1] = mpu.getAngleY();
  angleBatch[batchCounter][2] = mpu.getAngleZ();

  gyroBatch[batchCounter][0] = mpu.getGyroX();
  gyroBatch[batchCounter][1] = mpu.getGyroY();
  gyroBatch[batchCounter][2] = mpu.getGyroZ();

  accBatch[batchCounter][0] = mpu.getAccX();
  accBatch[batchCounter][1] = mpu.getAccY();
  accBatch[batchCounter][2] = mpu.getAccZ();

  tempBatch[batchCounter] = mpu.getTemp();
}

// -------------------- HTTP polling --------------------

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
      Serial.println("Exercise start received. Starting calibration.");

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

// -------------------- Calibration --------------------

void beginCalibration() {
  state = "calibrating";
  calibrationCount = 0;
  imuNeutralSum = 0.0;

  for (int i = 0; i < 3; i++) {
    calibrationSum[i] = 0;
  }

  smoothedWristAngle = 0.0;
  wristAngle = 0.0;
  minAngle = 0.0;
  maxAngle = 0.0;

  extensionScore = 0.0;
  flexionScore = 0.0;
  netWristScore = 0.0;
  motionConfidence = 0.0;
  wristMotion = "neutral";
}

void updateCalibration() {
  for (int i = 0; i < 3; i++) {
    calibrationSum[i] += filteredRaw[i];
  }

  if (mpuReady) {
    imuNeutralSum += getSelectedIMUAngle();
  }

  calibrationCount++;

  if (calibrationCount >= calibrationSamples) {
    for (int i = 0; i < 3; i++) {
      baselineRaw[i] = calibrationSum[i] / calibrationSamples;
      filteredRaw[i] = baselineRaw[i];
      filterInitialized[i] = true;
    }

    if (mpuReady) {
      neutralAngle = imuNeutralSum / calibrationSamples;
    } else {
      neutralAngle = 0.0;
    }

    smoothedWristAngle = 0.0;
    wristAngle = 0.0;
    minAngle = 0.0;
    maxAngle = 0.0;

    extensionScore = 0.0;
    flexionScore = 0.0;
    netWristScore = 0.0;
    motionConfidence = 0.0;
    wristMotion = "neutral";

    calibrated = true;
    state = "running";
    batchCounter = 0;

    Serial.print("Flex baseline calibrated: ");
    Serial.print(baselineRaw[0]);
    Serial.print(", ");
    Serial.print(baselineRaw[1]);
    Serial.print(", ");
    Serial.println(baselineRaw[2]);

    Serial.print("IMU neutral angle calibrated: ");
    Serial.println(neutralAngle);
  }
}

// -------------------- UDP sending --------------------

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

  // Uncomment for debugging:
  // Serial.println(json);
}

String buildJsonPayload() {
  String json = "{";

  json += "\"session_id\":\"" + sessionID + "\",";
  json += "\"batch_start_ms\":" + String(batchStartMs) + ",";
  json += "\"batch_end_ms\":" + String(batchEndMs) + ",";

  json += "\"sensor_map\":{";
  json += "\"gpio4\":\"extension_top_1\",";
  json += "\"gpio5\":\"extension_top_2\",";
  json += "\"gpio6\":\"flexion_bottom\"";
  json += "},";

  json += "\"data\":[";

  for (int i = 0; i < batchSize; i++) {
    json += "{";

    json += "\"flex\":{";
    json += "\"extension_top_1\":" + String(flexBatch[i][0], 1) + ",";
    json += "\"extension_top_2\":" + String(flexBatch[i][1], 1) + ",";
    json += "\"flexion_bottom\":" + String(flexBatch[i][2], 1);
    json += "},";

    json += "\"wrist\":{";
    json += "\"smoothed_angle\":" + String(wristBatch[i][0], 1) + ",";
    json += "\"raw_angle\":" + String(wristBatch[i][1], 1) + ",";
    json += "\"min_angle\":" + String(wristBatch[i][2], 1) + ",";
    json += "\"max_angle\":" + String(wristBatch[i][3], 1) + ",";
    json += "\"rom\":" + String(wristBatch[i][4], 1);
    json += "},";

    json += "\"fusion\":{";
    json += "\"extension_score\":" + String(fusionBatch[i][0], 1) + ",";
    json += "\"flexion_score\":" + String(fusionBatch[i][1], 1) + ",";
    json += "\"net_wrist_score\":" + String(fusionBatch[i][2], 1) + ",";
    json += "\"confidence\":" + String(fusionBatch[i][3], 1) + ",";
    json += "\"extension_flex_avg\":" + String(fusionBatch[i][4], 1) + ",";
    json += "\"extension_agreement\":" + String(fusionBatch[i][5], 1) + ",";
    json += "\"motion\":\"" + motionBatch[i] + "\"";
    json += "},";

    json += "\"imu\":{";

    json += "\"angle\":[";
    json += String(angleBatch[i][0], 1) + ",";
    json += String(angleBatch[i][1], 1) + ",";
    json += String(angleBatch[i][2], 1);
    json += "],";

    json += "\"gyro\":[";
    json += String(gyroBatch[i][0], 2) + ",";
    json += String(gyroBatch[i][1], 2) + ",";
    json += String(gyroBatch[i][2], 2);
    json += "],";

    json += "\"acc\":[";
    json += String(accBatch[i][0], 2) + ",";
    json += String(accBatch[i][1], 2) + ",";
    json += String(accBatch[i][2], 2);
    json += "],";

    json += "\"temp\":";
    json += String(tempBatch[i], 1);

    json += "}";

    json += "}";

    if (i < batchSize - 1) {
      json += ",";
    }
  }

  json += "]}";

  return json;
}

// -------------------- WiFi maintenance --------------------

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