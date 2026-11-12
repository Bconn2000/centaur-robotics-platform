// CENTAUR - 8 SONAR SENSOR TEST
// Arduino Mega 2560
// HC-SR04 Ultrasonic Sensors

const int NUM_SENSORS = 8;

// Sensor pins
const int trigPins[NUM_SENSORS] = {
  22, 24, 26, 28, 30, 32, 34, 36
};

const int echoPins[NUM_SENSORS] = {
  23, 25, 27, 29, 31, 33, 35, 37
};

// Distance measurements in centimeters
float distances[NUM_SENSORS];

void setup() {

  Serial.begin(115200);

  // Configure sensor pins
  for (int i = 0; i < NUM_SENSORS; i++) {
    pinMode(trigPins[i], OUTPUT);
    pinMode(echoPins[i], INPUT);

    digitalWrite(trigPins[i], LOW);
  }

  delay(1000);

  Serial.println("============================");
  Serial.println("   CENTAUR SONAR TEST");
  Serial.println("============================");
}

float readSonar(int sensor) {

  // Clear trigger
  digitalWrite(trigPins[sensor], LOW);
  delayMicroseconds(2);

  // Send 10 microsecond trigger
  digitalWrite(trigPins[sensor], HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPins[sensor], LOW);

  // Measure echo duration
  unsigned long duration =
    pulseIn(echoPins[sensor], HIGH, 25000UL);

  // No echo detected
  if (duration == 0) {
    return -1;
  }

  // Convert to centimeters
  float distance = duration * 0.0343 / 2.0;

  return distance;
}

void loop() {

  Serial.println();
  Serial.println("------ SONAR READINGS ------");

  for (int i = 0; i < NUM_SENSORS; i++) {

    distances[i] = readSonar(i);

    Serial.print("Sensor ");
    Serial.print(i + 1);
    Serial.print(": ");

    if (distances[i] < 0) {
      Serial.println("NO ECHO");
    }
    else {
      Serial.print(distances[i], 1);
      Serial.println(" cm");
    }

    // Reduce interference between sensors
    delay(60);
  }

  Serial.println("----------------------------");

  delay(500);
}
