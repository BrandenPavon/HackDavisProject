#include <Wire.h>
#include <MPU6050_light.h>

#define SDA_PIN 8
#define SCL_PIN 9

MPU6050 mpu(Wire);

// Change this depending on which axis matches your wrist motion
// Start with Angle X. If it is wrong, try Angle Y.
float neutralAngle = 0.0;
float wristAngle = 0.0;
float smoothedWristAngle = 0.0;

float minAngle = 0.0;
float maxAngle = 0.0;

bool neutralSet = false;

// Smoothing factor
// Lower = smoother but slower response
// Higher = faster but noisier
float alpha = 0.6;

void setup() {
  Serial.begin(115200);
  delay(1000);

  Wire.begin(SDA_PIN, SCL_PIN);

  byte status = mpu.begin();

  if (status != 0) {
    Serial.print("MPU6050 init failed. Status: ");
    Serial.println(status);
    while (1);
  }

  Serial.println("MPU6050 ready.");

  Serial.println("Keep the sensor still. Calculating offsets...");
  delay(1000);
  mpu.calcOffsets(true, true);
  Serial.println("Offsets calculated.");

  Serial.println("Place wrist in neutral position.");
  Serial.println("Hold still...");
  delay(3000);

  // Update several times so the angle estimate settles
  for (int i = 0; i < 100; i++) {
    mpu.update();
    delay(10);
  }

  // Use Angle X for first test
  // If the wrong motion is being measured, change this to getAngleY()
  neutralAngle = mpu.getAngleX();

  smoothedWristAngle = 0.0;
  minAngle = 0.0;
  maxAngle = 0.0;
  neutralSet = true;

  Serial.println("Neutral position saved.");
  Serial.println("Begin wrist movement.");
}

void loop() {
  mpu.update();

  if (!neutralSet) {
    return;
  }

  // Raw wrist angle relative to neutral
  // Change getAngleX() to getAngleY() if needed
  wristAngle = mpu.getAngleX() - neutralAngle;

  // Smooth the angle
  smoothedWristAngle = alpha * wristAngle + (1.0 - alpha) * smoothedWristAngle;

  // Track range of motion
  if (smoothedWristAngle < minAngle) {
    minAngle = smoothedWristAngle;
  }

  if (smoothedWristAngle > maxAngle) {
    maxAngle = smoothedWristAngle;
  }

  float totalRange = maxAngle - minAngle;

  Serial.print("Wrist Angle: ");
  Serial.print(smoothedWristAngle);
  Serial.print(" deg");

  Serial.print(" | Min: ");
  Serial.print(minAngle);
  Serial.print(" deg");

  Serial.print(" | Max: ");
  Serial.print(maxAngle);
  Serial.print(" deg");

  Serial.print(" | ROM: ");
  Serial.print(totalRange);
  Serial.println(" deg");

  delay(50);
}