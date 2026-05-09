const int flexPins[4] = {4, 5, 6, 7};  // GPIO1-GPIO4

//const unsigned long sampleIntervalMs = 50;  // 20 Hz
const unsigned long sampleIntervalMs = 500;  // 2 Hz
unsigned long lastSampleMs = 0;

// Slightly wider than theoretical range of ~1290 to ~2650
const int rawMin = 1100;
const int rawMax = 2800;

void setup() {
  Serial.begin(115200);

  analogReadResolution(12);          // 0 to 4095
  analogSetAttenuation(ADC_11db);    // ADC range up to about 3.3 V
}

void loop() {
  unsigned long now = millis();

  if (now - lastSampleMs >= sampleIntervalMs) {
    lastSampleMs = now;

    for (int i = 0; i < 4; i++) {
      int raw = analogRead(flexPins[i]);

      // Clamp raw value to expected range
      int clampedRaw = constrain(raw, rawMin, rawMax);

      // Scale to 0-100%
      // With your divider:
      // higher raw = lower flex resistance
      // lower raw = higher flex resistance
      // lower raw value = more bend = higher percentage
      float scaled = (rawMax - clampedRaw) * 100.0 / (rawMax - rawMin);

      Serial.print(raw);
      Serial.print(",");
      Serial.print(scaled, 1);

      if (i < 3) {
        Serial.print(",");
      }
    }

    Serial.println();
  }
}