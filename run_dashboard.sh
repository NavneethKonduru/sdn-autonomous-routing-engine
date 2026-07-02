#!/bin/bash

echo "======================================================="
echo "   Starting Autonomous Network Command Center...       "
echo "======================================================="

# Get the directory of this script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Determine Python command
if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
    PYTHON_CMD="python"
else
    echo "Error: Python is not installed or not in PATH."
    exit 1
fi

# Start the Python Backend (Flask-SocketIO)
echo "[1/2] Starting SDN Backend Controller on port 5000..."
$PYTHON_CMD "$DIR/src/applications/command_center/server.py" &
BACKEND_PID=$!

# Wait a moment to ensure backend is starting
sleep 2

# Start the React Frontend (Vite)
echo "[2/2] Starting React Frontend UI..."
FRONTEND_DIR="$DIR/src/applications/command_center/frontend"
cd "$FRONTEND_DIR"

if [ ! -d "node_modules" ]; then
    echo "Dependencies not found. Running npm install..."
    npm install
fi

npm run dev &
FRONTEND_PID=$!

echo "======================================================="
echo "   Command Center is RUNNING!                          "
echo "   Backend PID:  $BACKEND_PID                          "
echo "   Frontend PID: $FRONTEND_PID                         "
echo "   Access UI at: http://localhost:5173                 "
echo "                                                       "
echo "   Press Ctrl+C to stop both servers.                  "
echo "======================================================="

# Function to handle termination
cleanup() {
    echo ""
    echo "Shutting down servers..."
    kill $BACKEND_PID
    kill $FRONTEND_PID
    exit 0
}

# Trap Ctrl+C (SIGINT) and call cleanup
trap cleanup SIGINT SIGTERM

# Keep script running
wait $BACKEND_PID $FRONTEND_PID
