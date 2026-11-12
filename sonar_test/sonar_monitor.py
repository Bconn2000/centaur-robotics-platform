import serial
import re
import os

PORT = "/dev/ttyACM0"
BAUD = 115200

distances = ["NO ECHO"] * 8

print("Connecting to Arduino...")

with serial.Serial(PORT, BAUD, timeout=2) as ser:

    while True:
        line = ser.readline().decode(errors="ignore").strip()

        match = re.match(
            r"Sensor\s+(\d+):\s+(.+)", line
        )

        if match:
            sensor = int(match.group(1))
            value = match.group(2)

            if 1 <= sensor <= 8:
                distances[sensor - 1] = value

            # Refresh dashboard after sensor 8
            if sensor == 8:

                os.system("clear")

                print("=" * 42)
                print("        CENTAUR SONAR MONITOR")
                print("=" * 42)

                print(f"{'Sensor':<12}{'Distance':<17}Status")
                print("-" * 42)

                for i, distance in enumerate(distances):

                    status = (
                        "ACTIVE"
                        if distance != "NO ECHO"
                        else "--"
                    )

                    print(
                        f"Sonar {i+1:<6}"
                        f"{distance:<17}"
                        f"{status}"
                    )

                print("=" * 42)
                print("LIVE - Press Ctrl+C to exit")
