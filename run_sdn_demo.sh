#!/bin/bash
echo "Starting SDN Server on port 8890..."
python3 src/applications/chat_app/chat_app.py --server &
SERVER_PID=$!

echo "Waiting for server to start..."
sleep 2

echo "Starting Client and sending a message..."
echo -e "Hello from SDN Client!\n/status\n/quit" | python3 src/applications/chat_app/chat_app.py --client testuser

echo "Stopping Server..."
kill $SERVER_PID
echo "Done!"
