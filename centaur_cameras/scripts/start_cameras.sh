#!/bin/bash

# Centaur Robot - Three Camera Startup
# Thesis Workspace

set -e

BASE="$HOME/thesis_ws/src/centaur_cameras"
STREAMER="$BASE/mjpg-streamer/mjpg-streamer-experimental"
DASHBOARD="$BASE/dashboard"

PIDS=()

cleanup() {
    trap - INT TERM EXIT
    echo ""
    echo "Stopping Centaur cameras..."

    for pid in "${PIDS[@]}"; do
        kill "$pid" 2>/dev/null || true
    done

    wait 2>/dev/null || true
}

trap cleanup INT TERM EXIT

start_camera() {
    local device="$1"
    local port="$2"

    echo "Starting $device on port $port..."

    (
        cd "$STREAMER" || exit 1

        exec ./mjpg_streamer \
            -i "./input_uvc.so -d $device -r 1280x720 -f 20" \
            -o "./output_http.so -p $port -w ./www -l 127.0.0.1"
    ) &

    PIDS+=("$!")
}

echo "=================================="
echo "     CENTAUR CAMERA SYSTEM"
echo "=================================="

start_camera /dev/video0 8080
start_camera /dev/video2 8081
start_camera /dev/video4 8082

echo "Starting camera dashboard..."

(
    cd "$DASHBOARD" || exit 1
    exec python3 -m http.server 8090 --bind 127.0.0.1
) &

PIDS+=("$!")

echo ""
echo "Camera 1: http://localhost:8080"
echo "Camera 2: http://localhost:8081"
echo "Camera 3: http://localhost:8082"
echo ""
echo "Dashboard: http://localhost:8090"
echo ""
echo "Press Ctrl+C to stop everything."

wait
