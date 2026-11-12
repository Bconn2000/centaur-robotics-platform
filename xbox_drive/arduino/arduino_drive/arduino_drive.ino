#include <Servo.h>

Servo motorS1;
Servo motorS2;

const int S1_PIN = 9;
const int S2_PIN = 10;

// Brake SSR control pins
const int BRAKE_GND_RELAY = 7;
const int BRAKE_PWR_RELAY = 8;

// Initial testing limit.
// 1500 = stop; full range would be roughly 1000-2000.
const int MAX_OFFSET = 250;

const unsigned long FAILSAFE_MS = 500;
unsigned long lastCommand = 0;

String input = "";

bool brakesReleased = false;


void stopMotors() {
  motorS1.writeMicroseconds(1500);
  motorS2.writeMicroseconds(1500);
}


void engageBrakes() {
  // Stop motors before applying brakes
  stopMotors();

  digitalWrite(BRAKE_GND_RELAY, LOW);
  digitalWrite(BRAKE_PWR_RELAY, LOW);

  brakesReleased = false;

  Serial.println("BRAKES_ENGAGED");
}


void releaseBrakes() {
  digitalWrite(BRAKE_GND_RELAY, HIGH);
  digitalWrite(BRAKE_PWR_RELAY, HIGH);

  brakesReleased = true;

  Serial.println("BRAKES_RELEASED");
}


void setup() {
  Serial.begin(115200);

  motorS1.attach(S1_PIN);
  motorS2.attach(S2_PIN);

  // Set up brake relay pins
  pinMode(BRAKE_GND_RELAY, OUTPUT);
  pinMode(BRAKE_PWR_RELAY, OUTPUT);

  // SAFE STARTUP:
  // Motors stopped and brakes engaged
  stopMotors();

  digitalWrite(BRAKE_GND_RELAY, LOW);
  digitalWrite(BRAKE_PWR_RELAY, LOW);

  brakesReleased = false;

  lastCommand = millis();
}


void loop() {

  while (Serial.available()) {
    char c = Serial.read();

    if (c == '\n') {

      // ---------------------------
      // BRAKE COMMANDS
      // ---------------------------

      if (input == "BRAKE_RELEASE") {
        releaseBrakes();
        lastCommand = millis();
      }

      else if (input == "BRAKE_ENGAGE") {
        engageBrakes();
        lastCommand = millis();
      }

      // ---------------------------
      // MOTOR COMMANDS
      // ---------------------------

      else {
        int comma = input.indexOf(',');

        if (comma > 0) {

          int leftCommand =
              input.substring(0, comma).toInt();

          int rightCommand =
              input.substring(comma + 1).toInt();

          leftCommand =
              constrain(leftCommand, -100, 100);

          rightCommand =
              constrain(rightCommand, -100, 100);


          // IMPORTANT:
          // M1/S1 = RIGHT side
          // M2/S2 = LEFT side

          // Only allow movement when brakes
          // have been deliberately released.
          if (brakesReleased) {

            int s1Pulse =
                1500 -
                (rightCommand * MAX_OFFSET / 100);

            int s2Pulse =
                1500 -
                (leftCommand * MAX_OFFSET / 100);

            motorS1.writeMicroseconds(s1Pulse);
            motorS2.writeMicroseconds(s2Pulse);
          }

          else {
            stopMotors();
          }

          lastCommand = millis();
        }
      }

      input = "";
    }

    else {
      input += c;
    }
  }


  // Laptop communication fails for >250 ms:
  // stop motors.
  //
  // We're NOT automatically changing the brake
  // state here because the normal Python motor
  // packets provide the heartbeat.
  if (millis() - lastCommand > FAILSAFE_MS) {
    if (brakesReleased) {
        engageBrakes();
    } else {
        stopMotors();
    }
}
}
