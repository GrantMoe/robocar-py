#include <Servo.h>

#define HWSERIAL Serial1

const int steeringNeutral = 1600;
const int steeringMin = 1375;
const int steeringMax = 1825;
const int throttleNeutral = 1500;
const int throttleMin = 1150;
const int throttleMax = 1850;

int steeringByte = 127;
int throttleByte = 127;
int steeringMicroseconds;
int throttleMicroseconds;

const int steeringPin = 3;
const int throttlePin = 4;
Servo steeringServo;
Servo throttleServo;

bool isDriving = false;


void setup() {
  Serial.begin(9600);
  HWSERIAL.begin(115200);

  steeringServo.attach(steeringPin);
  throttleServo.attach(throttlePin);
  
}

void loop() {
  if (isDriving) {
    Serial.println("drive loop");
  
    steeringMicroseconds = map(steeringByte, 0, 255, steeringMin, steeringMax);
    throttleMicroseconds = map(throttleByte, 0, 255, throttleMin, throttleMax);

    Serial.println("Steering: " + String(steeringMicroseconds));
    Serial.println("Throttle: " + String(throttleMicroseconds));

    
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
    else if (firstChar == 'n') {
      steeringByte = HWSERIAL.parseInt();
      throttleByte = HWSERIAL.parseInt();
    }
    else if (firstChar == 'x') {
      steeringServo.writeMicroseconds(steeringNeutral);
      throttleServo.writeMicroseconds(throttleNeutral);
      isDriving = false;
      Serial.println("stopped driving");
    }
  }
}

   
