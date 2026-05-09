#include <Wire.h>

#define SDA_PIN 8
#define SCL_PIN 9

void setup() {
  Wire.begin(SDA_PIN, SCL_PIN);
}

void loop() {
  // put your main code here, to run repeatedly:

}
