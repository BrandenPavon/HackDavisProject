const int flexPin1 = 4;  // GPIO1
const int flexPin2 = 5;  // GPIO2

const unsigned long sampleIntervalMs = 50;  // 20 Hz
unsigned long lastSampleMs = 0;

// Calibrate these separately for each sensor
const int sensor1RawMin = 1100;
const int sensor1RawMax = 2800;

const int sensor2RawMin = 1100;
const int sensor2RawMax = 2800;

// Digital filter strength
// Lower alpha = smoother but slower
// Higher alpha = faster but noisier
const float alpha = 0.60;

float filteredRaw1 = 0;
float filteredRaw2 = 0;
bool filterInitialized = false;

float scaleToBendPercent(float rawValue, int rawMin, int rawMax) {
  int clampedRaw = constrain((int)rawValue, rawMin, rawMax);
  // Inverted scale:
  // lower raw value = more bend = higher percentage
  return (rawMax - clampedRaw) * 100.0 / (rawMax - rawMin);
}



void setup() {
  Serial.begin(115200);

  analogReadResolution(12);
  analogSetAttenuation(ADC_11db);
}



void loop() {
  unsigned long now = millis();

  if (now - lastSampleMs >= sampleIntervalMs) {
    lastSampleMs = now;

    int raw1 = analogRead(flexPin1);
    int raw2 = analogRead(flexPin2);

    if (!filterInitialized) {
      filteredRaw1 = raw1;
      filteredRaw2 = raw2;
      filterInitialized = true;
    } else {
      filteredRaw1 = alpha * raw1 + (1.0 - alpha) * filteredRaw1;
      filteredRaw2 = alpha * raw2 + (1.0 - alpha) * filteredRaw2;
    }

    float bend1 = scaleToBendPercent(filteredRaw1, sensor1RawMin, sensor1RawMax);
    float bend2 = scaleToBendPercent(filteredRaw2, sensor2RawMin, sensor2RawMax);

    float averageBend = (bend1 + bend2) / 2.0;

    // Serial Plotter format:
    // bend1 bend2 averageBend
    Serial.print(bend1, 1);
    Serial.print("\t");
    Serial.print(bend2, 1);
    Serial.print("\t");
    Serial.println(averageBend, 1);
  }
}