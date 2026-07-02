# Autonomous SDN Routing Engine 🚀

A full-stack, split-screen **Software-Defined Networking (SDN) simulation engine** built to visually and technically demonstrate the real-time advantages of centralized network intelligence over traditional decentralized routing protocols.

![SDN Dashboard Architecture](src/applications/command_center/frontend/src/assets/hero.png)

## 🌟 Overview
This project simulates an entire custom networking stack from the ground up, featuring a custom Python backend that powers both a headless **Terminal CLI Chat Application** and a stunning **React-based Web Dashboard**. 

It runs two simultaneous routing algorithms on identical D3.js physics-driven network topologies to actively compare how a standard IP network handles adverse conditions versus an SDN-controlled network.

## 🎯 Key Features

### 1. Dynamic Traffic Engineering (The "Traffic Jam")
- **Traditional Networking (Top Screen):** Uses unweighted BFS/Shortest Path routing. Blindly routes traffic into heavily congested links because it lacks global state awareness.
- **SDN Controller (Bottom Screen):** Leverages a God's-eye view of the network state. Dynamically applies Dijkstra's algorithm against real-time link weights to actively route packets *around* congestion.

### 2. Slow Convergence vs Instant Re-routing (The "Cut Wire")
- When a physical link is severed, traditional routers rely on slow gossip protocols to update routing tables. The simulation demonstrates this by sending packets into the severed link where they are dropped.
- The SDN Controller instantly detects port failures, pushes `FLOW_MOD` updates to the edge switches, and routes around the failure with zero packet loss.

### 3. Centralized Ingress Security
- Traditional networking often relies on endpoint security or distributed firewalls, allowing malicious packets to waste core network bandwidth before being dropped.
- Our SDN engine allows for instant, centralized **Firewall Bans**. A malicious user's packets trigger a `PACKET_IN` event at the edge switch and are instantly dropped via controller rules, neutralizing the threat before it touches the core network.

## 🛠️ Architecture Stack
- **Backend Core**: Python 3, custom Socket.IO application layer, simulated OpenFlow protocol, custom packet structuring.
- **Frontend Visualization**: React, Vite, D3.js Force Simulation Engine, Lucide Icons.
- **Communication**: Bidirectional low-latency WebSockets mapping Python events directly to React state hooks.

## 🚀 Getting Started

### 1. Launch the Visual Dashboard
To start the React frontend and Python backend simultaneously:

**On Mac/Linux:**
```bash
./run_dashboard.sh
```
**On Windows:**
```cmd
run_dashboard.bat
```
Then visit `http://localhost:5173` in your browser.

### 2. Launch the "Naked" Terminal App
Want to see the raw routing engine at work? You can use the engine as a purely terminal-based messaging application!

**Terminal 1 (Server):**
```bash
python3 src/applications/chat_app/chat_app.py --config configs/sdn_config.yaml --server
```
*(Note: By default, the server runs on port `8888`. However, if the Visual Dashboard is running in the background and occupying port `8888`, the standalone server will automatically find the next available port, such as `8889`.)*

**Terminal 2 & 3 (Clients):**
Look at what port your server started on, then connect your clients to that port using the `--port` flag (if it fell back to 8889):
```bash
python3 src/applications/chat_app/chat_app.py --client Alice --port 8889
python3 src/applications/chat_app/chat_app.py --client Bob --port 8889
```
*Tip: In a client terminal, type `/traffic s1 s2 20` to manually create a traffic jam, then send a message and watch the server console calculate the routing diversion!*

---
*Built as a capstone exploration into modern networking paradigms.*
