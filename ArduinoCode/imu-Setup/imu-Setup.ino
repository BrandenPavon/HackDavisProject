#include <Wire.h>
#include <MPU6050_light.h>

#define SDA_PIN 8
#define SCL_PIN 9

MPU6050 mpu(Wire);

void setup() {
  Serial.begin(115200);
  delay(1000);

  Wire.begin(SDA_PIN, SCL_PIN);

  byte status = mpu.begin();

  if (status != 0) {
    Serial.print("MPU6050 init failed. Status: ");
    Serial.println(status);
    return;
  }

  Serial.println("MPU6050 ready!");

  Serial.println("Keep sensor still, calculating offsets...");
  delay(1000);
  mpu.calcOffsets(true, true);
  Serial.println("Done.");
}

void loop() {
  mpu.update();

  Serial.print("Angle X: ");
  Serial.print(mpu.getAngleX());
  Serial.print(" | Angle Y: ");
  Serial.print(mpu.getAngleY());
  Serial.print(" | Angle Z: ");
  Serial.println(mpu.getAngleZ());

  Serial.print(" || Gyro X: ");
  Serial.print(mpu.getGyroX());
  Serial.print(" dps | Gyro Y: ");
  Serial.print(mpu.getGyroY());
  Serial.print(" dps | Gyro Z: ");
  Serial.print(mpu.getGyroZ());
  Serial.println(" dps");


  delay(100);
}