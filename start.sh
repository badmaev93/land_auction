#!/bin/bash

# Start the oTree web server in the background
otree prodserver1of2 &
WEB_PID=$!

# Start the oTree worker in the background
otree prodserver2of2 &
WORKER_PID=$!

# Function to kill child processes on exit
cleanup() {
    echo "Terminating child processes..."
    kill $WEB_PID $WORKER_PID 2>/dev/null
    exit 0
}
trap cleanup SIGTERM SIGINT

# Wait for any process to exit. If one dies, the script exits.
# This helps Render detect if the main process (web) or worker fails.
wait -n $WEB_PID $WORKER_PID
echo "One of the oTree processes exited. Exiting."
exit 1 # Exit with non-zero to indicate failure if a child process died
