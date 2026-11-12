#!/bin/bash

set -e

BASE="$HOME/thesis_ws/src/centaur_cameras"
MEDIAMTX="$BASE/mediamtx"
DASHBOARD="$BASE/webrtc_dashboard"

PIDS=()

cleanup() {
    trap - INT TERM EXIT

    echo ""
    echo "Stopping Centaur camera system..."

    for pid in "${PIDS[@]}"; do
        kill "$pid" 2>/dev/null || true
    done

    wait 2>/dev/null || true

    echo "Centaur camera system stopped."
}

trap cleanup INT TERM EXIT

start_camera() {
    local device="$1"
    local name="$2"
    local position="$3"

    echo "Starting $position ($name)..."

    gst-launch-1.0 -q \
        v4l2src device="$device" do-timestamp=true ! \
        image/jpeg,width=1280,height=720,framerate=20/1 ! \
        jpegdec ! \
        videoconvert ! \
        video/x-raw,format=I420 ! \
        queue max-size-buffers=2 max-size-bytes=0 max-size-time=0 leaky=downstream ! \
        x264enc tune=zerolatency speed-preset=ultrafast bitrate=1500 key-int-max=20 bframes=0 ! \
        video/x-h264,profile=baseline ! \
        h264parse ! \
        rtspclientsink location="rtsp://127.0.0.1:8554/$name" protocols=tcp &

    PIDS+=("$!")
}

echo "===================================="
echo "    CENTAUR FOUR-CAMERA SYSTEM      "
echo "===================================="

echo "Starting MediaMTX..."

(
    cd "$MEDIAMTX"
    exec ./mediamtx
) &

PIDS+=("$!")

echo "Waiting for MediaMTX..."

ready=false

for attempt in $(seq 1 30); do
    if (echo > /dev/tcp/127.0.0.1/8554) 2>/dev/null; then
        ready=true
        break
    fi
    sleep 1
done

if [ "$ready" != true ]; then
    echo "ERROR: MediaMTX did not start."
    exit 1
fi

USB_BASE="/dev/v4l/by-path/pci-0000:00:14.0-usb-0"

start_camera "${USB_BASE}:2:1.0-video-index0" camera1 "FRONT LEFT"
start_camera "${USB_BASE}:1:1.0-video-index0" camera2 "FRONT RIGHT"
start_camera "${USB_BASE}:4:1.0-video-index0" camera3 "REAR LEFT"
start_camera "${USB_BASE}:3:1.0-video-index0" camera4 "REAR RIGHT"

echo "Starting dashboard..."

(
    cd "$DASHBOARD"
    exec python3 -m http.server 8091 --bind 0.0.0.0
) &

PIDS+=("$!")

echo ""
echo "===================================="
echo "       CENTAUR SYSTEM READY         "
echo "===================================="
echo ""
echo "Dashboard: http://localhost:8091"
echo ""
echo "Camera 1: FRONT LEFT  (USB 1)"
echo "Camera 2: FRONT RIGHT (USB 2)"
echo "Camera 3: REAR LEFT   (USB 3)"
echo "Camera 4: REAR RIGHT  (USB 4)"
echo ""
echo "Press Ctrl+C to stop everything."
echo ""

wait
