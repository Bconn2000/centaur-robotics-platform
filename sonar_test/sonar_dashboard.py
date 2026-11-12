import tkinter as tk
import serial
import re
import sys
import time

# ==========================================
# CENTAUR SONAR PROXIMITY DASHBOARD
# ==========================================

PORT = sys.argv[1] if len(sys.argv) > 1 else "/dev/ttyUSB0"
BAUD = 115200

ROBOT_WIDTH = 26    # inches
ROBOT_LENGTH = 47   # inches

# Distance thresholds (inches)
RED_LIMIT = 6
ORANGE_LIMIT = 12
YELLOW_LIMIT = 24

# Sensor arrangement:
#
#             FRONT
#           S1     S5
#       S2             S6
#       S3             S7
#           S4     S8
#              REAR

COLORS = {
    "RED": "#E53935",
    "ORANGE": "#FB8C00",
    "YELLOW": "#FDD835",
    "GREEN": "#43A047",
    "UNKNOWN": "#757575"
}

distances = [None] * 8
last_seen = [0.0] * 8

# ==========================================
# GUI SETUP
# ==========================================

root = tk.Tk()
root.title("CENTAUR - Sonar Proximity Dashboard")
root.geometry("950x850")
root.minsize(750, 700)
root.configure(bg="#151A22")

title = tk.Label(
    root,
    text="CENTAUR SONAR PROXIMITY SYSTEM",
    font=("Arial", 22, "bold"),
    fg="white",
    bg="#151A22"
)
title.pack(pady=(15, 5))

subtitle = tk.Label(
    root,
    text="8 Ultrasonic Sensors | 26\" Wide × 47\" Long",
    font=("Arial", 12),
    fg="#B0BEC5",
    bg="#151A22"
)
subtitle.pack()

canvas = tk.Canvas(
    root,
    width=900,
    height=650,
    bg="#151A22",
    highlightthickness=0
)
canvas.pack(pady=10, fill="both", expand=True)

status_label = tk.Label(
    root,
    text="Connecting to Arduino...",
    font=("Arial", 11),
    fg="#B0BEC5",
    bg="#151A22"
)
status_label.pack(pady=5)

# ==========================================
# DISTANCE PROCESSING
# ==========================================

def get_status(distance):
    if distance is None or distance < 0:
        return "UNKNOWN"

    if distance <= RED_LIMIT:
        return "RED"
    elif distance <= ORANGE_LIMIT:
        return "ORANGE"
    elif distance <= YELLOW_LIMIT:
        return "YELLOW"
    else:
        return "GREEN"


def format_distance(distance):
    if distance is None or distance < 0:
        return "NO ECHO"

    return f"{distance:.1f} in"


# ==========================================
# DRAW DASHBOARD
# ==========================================

def draw_dashboard():
    canvas.delete("all")

    w = max(canvas.winfo_width(), 750)
    h = max(canvas.winfo_height(), 600)

    cx = w / 2
    cy = h / 2

    # Maintain actual robot proportions
    scale = min(7.0, (h - 180) / ROBOT_LENGTH)

    rw = ROBOT_WIDTH * scale
    rh = ROBOT_LENGTH * scale

    left = cx - rw / 2
    right = cx + rw / 2
    top = cy - rh / 2
    bottom = cy + rh / 2

    zone_depth = 85
    gap = 8

    # Robot body
    canvas.create_rectangle(
        left, top, right, bottom,
        fill="#263746",
        outline="#90A4AE",
        width=3
    )

    canvas.create_text(
        cx, cy - 30,
        text="CENTAUR",
        fill="white",
        font=("Arial", 18, "bold")
    )

    canvas.create_text(
        cx, cy + 5,
        text='26" × 47"',
        fill="#B0BEC5",
        font=("Arial", 13)
    )

    canvas.create_text(
        cx, cy + 35,
        text="TOP VIEW",
        fill="#90A4AE",
        font=("Arial", 10)
    )

    canvas.create_text(
        cx, top - 110,
        text="FRONT",
        fill="white",
        font=("Arial", 13, "bold")
    )

    canvas.create_text(
        cx, bottom + 110,
        text="REAR",
        fill="white",
        font=("Arial", 13, "bold")
    )

    def zone(sensor, x1, y1, x2, y2):
        distance = distances[sensor - 1]
        status = get_status(distance)
        color = COLORS[status]

        canvas.create_rectangle(
            x1, y1, x2, y2,
            fill=color,
            outline="#151A22",
            width=3
        )

        tx = (x1 + x2) / 2
        ty = (y1 + y2) / 2

        text_color = (
            "#17202A" if status == "YELLOW"
            else "white"
        )

        canvas.create_text(
            tx, ty - 12,
            text=f"S{sensor}",
            fill=text_color,
            font=("Arial", 13, "bold")
        )

        canvas.create_text(
            tx, ty + 12,
            text=format_distance(distance),
            fill=text_color,
            font=("Arial", 11, "bold")
        )

    # Front sensors
    zone(1, left, top - zone_depth, cx - gap / 2, top - gap)
    zone(5, cx + gap / 2, top - zone_depth, right, top - gap)

    # Rear sensors
    zone(4, left, bottom + gap, cx - gap / 2, bottom + zone_depth)
    zone(8, cx + gap / 2, bottom + gap, right, bottom + zone_depth)

    # Side sensors
    middle_y = (top + bottom) / 2

    zone(2, left - zone_depth, top, left - gap, middle_y - gap / 2)
    zone(3, left - zone_depth, middle_y + gap / 2, left - gap, bottom)

    zone(6, right + gap, top, right + zone_depth, middle_y - gap / 2)
    zone(7, right + gap, middle_y + gap / 2, right + zone_depth, bottom)


# ==========================================
# SERIAL CONNECTION
# ==========================================

try:
    ser = serial.Serial(PORT, BAUD, timeout=0)
    connection_error = None

except serial.SerialException as e:
    ser = None
    connection_error = str(e)


def update_readings():
    global ser

    if ser is not None:
        try:
            # Process a limited number of lines per GUI update
            for _ in range(40):
                if ser.in_waiting == 0:
                    break

                line = ser.readline().decode(
                    errors="ignore"
                ).strip()

                match = re.match(
                    r"Sensor\s+(\d+):\s+(.+)",
                    line
                )

                if not match:
                    continue

                sensor = int(match.group(1))
                value = match.group(2).strip()

                if not 1 <= sensor <= 8:
                    continue

                index = sensor - 1

                if value == "NO ECHO":
                    distances[index] = None
                else:
                    number = re.search(
                        r"[-+]?\d+(?:\.\d+)?",
                        value
                    )

                    if number:
                        cm = float(number.group())
                        distances[index] = (
                            cm / 2.54 if cm >= 0 else None
                        )

                last_seen[index] = time.monotonic()

            # Mark stale sensors as unknown
            now = time.monotonic()

            for i in range(8):
                if now - last_seen[i] > 4:
                    distances[i] = None

            status_label.config(
                text=f"CONNECTED | {PORT} | 115200 baud",
                fg="#66BB6A"
            )

        except (serial.SerialException, OSError) as e:
            ser.close()
            ser = None
            status_label.config(
                text=f"SERIAL DISCONNECTED: {e}",
                fg="#EF5350"
            )

    else:
        status_label.config(
            text=f"NOT CONNECTED: {connection_error or 'Serial disconnected'}",
            fg="#EF5350"
        )

    draw_dashboard()

    root.after(100, update_readings)


# ==========================================
# START
# ==========================================

canvas.bind("<Configure>", lambda event: draw_dashboard())

update_readings()

def close_app():
    if ser is not None and ser.is_open:
        ser.close()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", close_app)
root.mainloop()
