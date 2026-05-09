const int flexPin = 4;  // GPIO1

const unsigned long sampleIntervalMs = 50;  // 20 Hz
unsigned long lastSampleMs = 0;

// Slightly wider than theoretical range of ~1290 to ~2650
const int rawMin = 1100;
const int rawMax = 2650;

// Digital low-pass filter - Used exponential moving average
// Lower alpha = smoother but slower
// Higher alpha = faster but noisier
const float alpha = 0.40;

float filteredRaw = 0;
bool filterInitialized = false;

void setup() {
  Serial.begin(115200);

  analogReadResolution(12);          // ADC raw range: 0 to 4095
  analogSetAttenuation(ADC_11db);    // Allows reading up to about 3.3 V
}

void loop() {
  unsigned long now = millis();

  if (now - lastSampleMs >= sampleIntervalMs) {
    lastSampleMs = now;

    int raw = analogRead(flexPin);

    // Initialize filter on first reading
    if (!filterInitialized) {
      filteredRaw = raw;
      filterInitialized = true;
    } else {
      filteredRaw = alpha * raw + (1.0 - alpha) * filteredRaw;
    }

    int clampedRaw = constrain((int)filteredRaw, rawMin, rawMax);

    // Inverted scale:
    // lower raw value = more bend = higher percentage
    float bendPercent = (rawMax - clampedRaw) * 100.0 / (rawMax - rawMin);

    Serial.print("raw=");
    Serial.print(raw);

    Serial.print(", filtered=");
    Serial.print(filteredRaw, 1);

    Serial.print(", bendPercent=");
    Serial.println(bendPercent, 1);
  }
}