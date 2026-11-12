import pygame
import serial
import time

PORT = "/dev/ttyACM0"
BAUD = 115200
DEADZONE = 0.12

pygame.init()
pygame.joystick.init()

if pygame.joystick.get_count() == 0:
    raise RuntimeError("No Xbox controller detected")

controller = pygame.joystick.Joystick(0)
controller.init()

arduino = serial.Serial(PORT, BAUD, timeout=0.1)
time.sleep(2)

print("Controller:", controller.get_name())
print("Arduino:", PORT)
print()
print("TANK DRIVE")
print("Left stick Y  = Left motors")
print("Right stick Y = Right motors")
print("X button      = Toggle brakes")
print("CTRL+C        = Stop")
print()

# Start assuming brakes are engaged
brakes_released = False
last_x = False


def apply_deadzone(value):
    if abs(value) < DEADZONE:
        return 0.0
    return value


try:
    while True:

        pygame.event.pump()

        # --------------------------------
        # X BUTTON - BRAKE TOGGLE
        # --------------------------------

        # Xbox X is normally button 2 in pygame
        x_pressed = controller.get_button(3)

        # Only toggle when X changes from
        # not pressed -> pressed
        if x_pressed and not last_x:

            brakes_released = not brakes_released

            if brakes_released:

                # Stop motors first
                arduino.write(b"0,0\n")
                time.sleep(0.05)

                # Release brakes
                arduino.write(b"BRAKE_RELEASE\n")

                print()
                print("*** BRAKES RELEASED ***")
                print()

            else:

                # Stop motors before engaging brakes
                arduino.write(b"0,0\n")
                time.sleep(0.05)

                # Engage brakes
                arduino.write(b"BRAKE_ENGAGE\n")

                print()
                print("*** BRAKES ENGAGED ***")
                print()

        last_x = x_pressed


        # --------------------------------
        # TANK DRIVE
        # --------------------------------

        # Up is -1 from Xbox controller,
        # so invert it to make forward positive.

        left_stick = apply_deadzone(
            -controller.get_axis(1)
        )

        right_stick = apply_deadzone(
            -controller.get_axis(3)
        )

        left_cmd = round(left_stick * 100)
        right_cmd = round(right_stick * 100)


        # If brakes are engaged, don't send
        # movement commands.
        if not brakes_released:
            left_cmd = 0
            right_cmd = 0


        message = f"{left_cmd},{right_cmd}\n"

        arduino.write(message.encode())


        brake_status = (
            "RELEASED"
            if brakes_released
            else "ENGAGED"
        )

        print(
            f"LEFT: {left_cmd:+4d}    "
            f"RIGHT: {right_cmd:+4d}    "
            f"BRAKES: {brake_status}"
        )


        time.sleep(0.05)


except KeyboardInterrupt:

    print("\nStopping...")

    # Stop motors FIRST
    arduino.write(b"0,0\n")
    time.sleep(0.1)

    # Engage brakes
    arduino.write(b"BRAKE_ENGAGE\n")
    time.sleep(0.1)

    arduino.close()
    pygame.quit()

    print("MOTORS STOPPED")
    print("BRAKES ENGAGED")
