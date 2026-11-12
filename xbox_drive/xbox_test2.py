
import pygame
import serial
import time

PORT = "/dev/ttyACM0"
BAUD = 115200

LEFT_AXIS = 1
RIGHT_AXIS = 3
BRAKE_BUTTON = 3

DEADZONE = 0.12
COMMAND_LIMIT = 100  

pygame.init()
pygame.joystick.init()

if pygame.joystick.get_count() == 0:
    raise RuntimeError("No controller detected")

controller = pygame.joystick.Joystick(0)
controller.init()

arduino = None
brakes_released = False
last_x = False

def deadzone(value):
    return 0.0 if abs(value) < DEADZONE else value

def send(message):
    arduino.write((message + "\n").encode())

try:
    arduino = serial.Serial(PORT, BAUD, timeout=0.02)
    time.sleep(2)

    print("Controller:", controller.get_name())
    print("Arduino:", PORT)
    print("DIAGNOSTIC TANK DRIVE")
    print("Left stick = S2 / M2")
    print("Right stick = S1 / M1")
    print("X = Toggle brakes")
    print("Ctrl+C = Stop")

    # Explicitly request a safe starting state
    send("0,0")
    send("BRAKE_ENGAGE")

    while True:
        pygame.event.pump()

        x_pressed = bool(controller.get_button(BRAKE_BUTTON))

        if x_pressed and not last_x:
            send("0,0")
            time.sleep(0.05)

            if brakes_released:
                send("BRAKE_ENGAGE")
                brakes_released = False
            else:
                send("BRAKE_RELEASE")
                brakes_released = True

        last_x = x_pressed

        left = round(
            deadzone(-controller.get_axis(LEFT_AXIS))
            * COMMAND_LIMIT
        )

        right = round(
            deadzone(-controller.get_axis(RIGHT_AXIS))
            * COMMAND_LIMIT
        )

        if not brakes_released:
            left = 0
            right = 0

        send(f"{left},{right}")

        # Display Arduino diagnostics
        while arduino.in_waiting:
            line = arduino.readline().decode(
                errors="replace"
            ).strip()

            if line:
                print("ARDUINO:", line)

                if line == "BRAKES_ENGAGED":
                    brakes_released = False

        print(
            f"PYTHON: LEFT={left:+d} "
            f"RIGHT={right:+d} "
            f"BRAKES_REQUESTED={brakes_released}"
        )

        time.sleep(0.05)

except KeyboardInterrupt:
    print("\nStopping controller...")

finally:
    if arduino is not None and arduino.is_open:
        try:
            send("0,0")
            send("BRAKE_ENGAGE")
            arduino.flush()
        finally:
            arduino.close()

    pygame.quit()
    print("Controller stopped")
