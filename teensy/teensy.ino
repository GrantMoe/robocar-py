#include <PulsePosition.h>

#define HWSERIAL Serial1

PulsePositionInput myIn;

void setup() {
  myIn.begin(20);
  Serial.begin(115200); // USB so speed ignored
  HWSERIAL.begin(115200);
}

int count=0;

void loop() {
  int i, num, incomingByte;
  if (HWSERIAL.available() > 0) {
    incomingByte = HWSERIAL.read();
    Serial.print("UART received: ");
    Serial.println(incomingByte, DEC);
//    HWSERIAL.print("UART received:");
//    HWSERIAL.println(incomingByte, DEC);
  }  
  // Every time new data arrives, simply print it
  // to the Arduino Serial Monitor.
  num = myIn.available();
  if (num > 0) {
    for (i=1; i <= num; i++) {
      float val = myIn.read(i);
      int int_val = int(val) + 1;
      HWSERIAL.print(int_val);
      if (i != num){
        HWSERIAL.print(",");
      }
    }
    HWSERIAL.println();
  }
}