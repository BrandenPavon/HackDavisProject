const int FLEX_PIN = 4;
int flexMin = 0;      // reading when sensor is straight
int flexMax = 4095;   // reading when sensor is fully bent


void setup() {
  // put your setup code here, to run once:
  Serial.begin(9600);
  delay(1000);

  analogReadResolution(12); // ESP32-S3 ADC: 0 to 4095

  // Optional but useful: allows reading close to 3.3V
  analogSetPinAttenuation(FLEX_PIN, ADC_11db);
}

void loop() {
  int raw = analogRead(FLEX_PIN);

  // Convert raw ADC reading to voltage
  float voltage = raw * (3.3 / 4095.0);

  // Convert to percent bend based on calibration values
  int bendPercent = map(raw, flexMin, flexMax, 0, 100);
  bendPercent = constrain(bendPercent, 0, 100);

  Serial.print("Raw: ");
  Serial.print(raw);

  Serial.print(" | Voltage: ");
  Serial.print(voltage, 3);
  Serial.print(" V");

  Serial.print(" | Bend: ");
  Serial.print(bendPercent);
  Serial.println("%");

  delay(100);

}
