# ScamShield Social Media App

A complete WebRTC-based Social Media Application built with React, Node.js, and Capacitor, natively integrated with the local ScamShield Edge AI microservice.

## Architecture

1. **Frontend (Client):** React 18, Vite, TailwindCSS. (WebRTC, MediaRecorder APIs). Can be built into a mobile APK via Capacitor.
2. **Backend (Server):** Node.js, Express, Socket.io. Handles real-time chat relay and WebRTC signaling (SDP offers/answers).
3. **Edge AI (Microservice):** FastAPI wrapper around the core ScamShield Python SDK. Performs local multi-modal analysis (Audio/Video/Text).

## How to Run

You need **three terminal windows** to run the full stack locally:

### Terminal 1: Start the Edge AI (Python)
`ash
cd app/edge_ai
pip install fastapi uvicorn python-multipart
python main.py
`
*(Runs on port 8002)*

### Terminal 2: Start the Signaling Server (Node.js)
`ash
cd app/server
npm install
npm start
`
*(Runs on port 5000)*

### Terminal 3: Start the Web App (React)
`ash
cd app/client
npm install
npm run dev
`
*(Runs on http://localhost:5173)*

## How to build an Android APK
Because we used Capacitor, your React app is already configured to be a mobile app!
1. cd app/client
2. 
pm run build
3. 
pm install @capacitor/android
4. 
px cap add android
5. 
px cap sync
6. 
px cap open android (This opens Android Studio where you can hit "Build APK").
