
#include <Servo.h>

Servo motorS1;
Servo motorS2;

// Arduino Mega connections
const int S1_PIN = 9;    // Right motors
const int S2_PIN = 10;   // Left motors

const int BRAKE_GND_RELAY = 7;
const int BRAKE_PWR_RELAY = 8;

const int NEUTRAL = 1500;
const int MAX_OFFSET = 500; // 30% command range

const unsigned long FAILSAFE_MS = 250;

unsigned long lastCommand = 0;
bool brakesReleased = false;

char input[40];
int inputIndex = 0;

void stopMotors() {
  motorS1.writeMicroseconds(NEUTRAL);
  motorS2.writeMicroseconds(NEUTRAL);
}

void engageBrakes() {
  stopMotors();

  digitalWrite(BRAKE_GND_RELAY, LOW);
  digitalWrite(BRAKE_PWR_RELAY, LOW);

  brakesReleased = false;
  Serial.println("BRAKES_ENGAGED");
}

void releaseBrakes() {
  stopMotors();

  digitalWrite(BRAKE_GND_RELAY, HIGH);
  digitalWrite(BRAKE_PWR_RELAY, HIGH);

  brakesReleased = true;
  Serial.println("BRAKES_RELEASED");
}

void processCommand(char *command) {

  if (strcmp(command, "BRAKE_RELEASE") == 0) {
    releaseBrakes();
    lastCommand = millis();
    return;
  }

  if (strcmp(command, "BRAKE_ENGAGE") == 0) {
    engageBrakes();
    lastCommand = millis();
    return;
  }

  int left, right;
  char extra;

  // Reject malformed commands
  if (sscanf(command, "%d,%d%c",
             &left, &right, &extra) != 2) {
    Serial.println("INVALID_COMMAND");
    return;
  }

  left = constrain(left, -100, 100);
  right = constrain(right, -100, 100);

  int s1Pulse = NEUTRAL;
  int s2Pulse = NEUTRAL;

  if (brakesReleased) {
    s1Pulse = NEUTRAL - right * MAX_OFFSET / 100;
    s2Pulse = NEUTRAL - left * MAX_OFFSET / 100;
  }

  motorS1.writeMicroseconds(s1Pulse);
  motorS2.writeMicroseconds(s2Pulse);

  lastCommand = millis();

  Serial.print("LEFT=");
  Serial.print(left);
  Serial.print(" RIGHT=");
  Serial.print(right);
  Serial.print(" S1=");
  Serial.print(s1Pulse);
  Serial.print(" S2=");
  Serial.println(s2Pulse);
}

void setup() {
  // Set relay output levels before enabling pins
  digitalWrite(BRAKE_GND_RELAY, LOW);
  digitalWrite(BRAKE_PWR_RELAY, LOW);

  pinMode(BRAKE_GND_RELAY, OUTPUT);
  pinMode(BRAKE_PWR_RELAY, OUTPUT);

  motorS1.attach(S1_PIN);
  motorS2.attach(S2_PIN);

  stopMotors();

  Serial.begin(115200);
  lastCommand = millis();

  Serial.println("ARDUINO_READY");
}

void loop() {

  while (Serial.available() > 0) {
    char c = Serial.read();

    if (c == '\n') {
      input[inputIndex] = '\0';
      processCommand(input);
      inputIndex = 0;
    }
    else if (c != '\r') {
      if (inputIndex < sizeof(input) - 1) {
        input[inputIndex++] = c;
      } else {
        inputIndex = 0;
        Serial.println("INPUT_OVERFLOW");
      }
    }
  }

  if (millis() - lastCommand > FAILSAFE_MS) {
    if (brakesReleased) {
      engageBrakes();
    } else {
      stopMotors();
    }
  }
}
