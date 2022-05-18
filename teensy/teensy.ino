#include <Servo.h>
#include <Teensy-ICM-20948.h>

#define HWSERIAL Serial1

#define SPI_PORT SPI
#define CS_PIN 2

#define STR_IN_PIN 5
#define THR_IN_PIN 6
#define SW_IN_PIN 7

#define STR_SRV_PIN 3
#define THR_SRV_PIN 4

#define MIN_PULSE 1000
#define NEU_PULSE 1500
#define MAX_PULSE 2000

#define MIN_STR 1375
#define NEU_STR 1600
#define MAX_STR 1825

#define MIN_THR 1150
#define NEU_THR 1500
#define MAX_THR 1850

#define MIN_OUT_INT 0
#define MAX_OUT_INT 1024

unsigned long str_in = 0;
unsigned long thr_in = 0;
unsigned long sw_in = 0;

int str_out;
int thr_out;

int str_msec_out;
int thr_msec_out;

Servo steeringServo;
Servo throttleServo;

TeensyICM20948 icm20948;

TeensyICM20948Settings icmSettings =
{
  .cs_pin = 10,                  // SPI chip select pin
  .spi_speed = 7000000,          // SPI clock speed in Hz, max speed is 7MHz
  .mode = 1,                     // 0 = low power mode, 1 = high performance mode
  .enable_gyroscope = false,      // Enables gyroscope output
  .enable_accelerometer = true,  // Enables accelerometer output
  .enable_magnetometer = false,   // Enables magnetometer output
  .enable_quaternion = true,     // Enables quaternion output
  .gyroscope_frequency = 1,      // Max frequency = 225, min frequency = 1
  .accelerometer_frequency = 255,  // Max frequency = 225, min frequency = 1
  .magnetometer_frequency = 1,   // Max frequency = 70, min frequency = 1
  .quaternion_frequency = 255     // Max frequency = 225, min frequency = 50
};


bool is_driving = false;
bool auto_mode = false;

void setup() {
  
  Serial.begin(9600);
  HWSERIAL.begin(115200);

  icm20948.init(icmSettings);

  steeringServo.attach(STR_SRV_PIN);
  throttleServo.attach(THR_SRV_PIN);
}

void loop() {

  str_in = pulseIn(STR_IN_PIN);
  thr_in = pulseIn(THR_IN_PIN);
  sw_in = pulseIn(SW_IN_PIN);

  if (isDriving) {
    Serial.println("drive loop");
  
    str_msec_out = map(steeringInt, MIN_OUT_INT, MAX_OUT_INT, MIN_STR, MAX_STR);
    thr_msec_out = map(throttleInt, MIN_OUT_INT, MAX_OUT_INT, MIN_THR, MAX_THR);

    Serial.println("Steering: " + String(str_msec_out));
    Serial.println("Throttle: " + String(thr_msec_out));

    steeringServo.writeMicroseconds(steeringMicroseconds);
    throttleServo.writeMicroseconds(throttleMicroseconds);
  }
//  delay(0.1);
}

void serialEvent1() {

  if (HWSERIAL.available() > 0) {
    char firstChar = (char) HWSERIAL.read();
    if (firstChar == 's') {
      isDriving = true;
      Serial.println("started driving");
    }
    else if (firstChar == 'g') {
      if HWSERIAL.availableForWrite() {
       HWSERIAL.println("i," + steeringIn + "," + throttleIn + "," + switchIn); 
      }
    }
    else if (firstChar == 'o') {
      steeringInt = HWSERIAL.parseInt();
      throttleInt = HWSERIAL.parseInt();
    }
    else if (firstChar == 'x') {
      steeringServo.writeMicroseconds(NEUTRAL_STEERING);
      throttleServo.writeMicroseconds(NEUTRAL_THROTTLE);
      isDriving = false;
      Serial.println("stopped driving");
    }
  }
}

   
