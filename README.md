# 🛡️ ScamShield — Edge AI Scam & Deepfake Detection SDK

> **Privacy-first, real-time, multimodal scam detection that runs entirely on the user's device.**

ScamShield is a multimodal AI system that protects users from UPI fraud, OTP scams, bank phishing, AI voice cloning, deepfake video calls, and manipulated images — all in **under 100ms** with **zero network latency**.

Raw content (audio, text, video, images) **never leaves the device**. Only mathematical feature vectors are escalated to the cloud for complex threats.

---

## 🏗️ Architecture

ScamShield uses a **two-stage detection pipeline**:

```
┌──────────────────────────────────────────────────────────────────┐
│                      USER DEVICE (Edge AI)                       │
│                                                                  │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│   │ TextGate │  │AudioGate │  │VideoGate │  │ImageGate │       │
│   │ MiniLM   │  │ Whisper  │  │ OpenCV   │  │Tesseract │       │
│   │ Cosine   │  │ Librosa  │  │MediaPipe │  │ OCR+ELA  │       │
│   └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘       │
│        └──────────────┴──────────────┴──────────────┘            │
│                          │                                       │
│                   Threat Fusion Engine                            │
│              ┌───────────┴───────────┐                           │
│              │  Score < 0.55 → ✅ SAFE                           │
│              │  Score ≥ 0.55 → 🔴 ALERT                         │
│              │           ↓ vectors only                          │
│              └───────────┬───────────┘                           │
│                          │ Cloud Escalation (optional)           │
└──────────────────────────┼───────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────────────┐
│                  CLOUD (Render — Singapore)                       │
│                                                                  │
│   Swytchcode → Lyzr AI Agents → Tavily OSINT → Final Verdict   │
│   (Router)     (4 Fraud Agents)  (URL Check)    → PostgreSQL    │
└──────────────────────────────────────────────────────────────────┘
```

**Stage 1 — Edge (On-Device):** Four AI gates analyse content locally using lightweight models (~300 MB total). Alerts appear in under 100ms.

**Stage 2 — Cloud (Optional):** For novel or complex threats, scrubbed feature vectors (never raw content) are routed to a multi-agent AI council on Render for a secondary verdict.

---

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| **🔒 Zero-Latency Edge AI** | All 4 gates run locally — text, audio, video, image — with alerts in < 100ms and no internet dependency |
| **🎙️ AI Voice Clone Detection** | DAVE Architecture analyses MFCC variance and spectral flux to detect AI-generated voices (ElevenLabs, etc.) |
| **📹 Deepfake Video Detection** | MediaPipe 468-point face mesh detects lip-sync mismatches, blink anomalies, and frame jitter |
| **🧠 Dynamic Trust Engine** | SQLite-backed reputation system adjusts AI sensitivity per contact — known contacts get relaxed thresholds, strangers get maximum vigilance |
| **🌐 Multi-Agent Cloud Council** | Lyzr AI agents + Tavily OSINT analyse escalated vectors in parallel for complex threats |
| **🔐 Privacy by Architecture** | Raw content never leaves the device. Cloud only receives mathematical vectors. GDPR/DPDPA compliant by design |
| **📴 Fully Offline Capable** | After initial model download, the entire system works in airplane mode |

---

## 📁 Project Structure

```
ScamShieldV3/
├── sdk/                        # Core Python SDK
│   └── scamshield/
│       ├── gate/               # AI Detection Gates
│       │   ├── text_gate.py    # Semantic intent analysis (MiniLM + Cosine)
│       │   ├── audio_gate.py   # Voice clone detection (Whisper + Librosa)
│       │   ├── video_gate.py   # Deepfake detection (OpenCV + MediaPipe)
│       │   ├── image_gate.py   # Forgery detection (ELA + OCR + FFT)
│       │   ├── context_engine.py  # Trust scoring (SQLite)
│       │   ├── preprocessor.py # De-obfuscation & entity extraction
│       │   ├── c2pa_gate.py    # Content authenticity verification
│       │   └── stream_gate.py  # Real-time audio streaming
│       ├── privacy/            # PII scrubbing layer
│       ├── explain/            # SmolLM-135M local explainer
│       ├── cloud/              # Cloud escalation client
│       └── client.py           # Main ScamShield SDK client
│
├── app/                        # Demo Application
│   ├── frontend/               # React + Vite + TailwindCSS dashboard
│   ├── backend/                # Node.js WebSocket signaling server
│   └── edge_ai/               # FastAPI edge AI server (port 8001)
│
├── cloud/                      # Cloud API (Render deployment)
│   ├── app/
│   │   ├── api/               # FastAPI endpoints (detection, incidents)
│   │   ├── services/          # Lyzr, Tavily, Swytchcode integrations
│   │   └── db/                # PostgreSQL models
│   ├── swytchcode/            # Pipeline orchestration config
│   ├── render.yaml            # Render deployment blueprint
│   └── requirements.txt
│
├── tests/
│   └── samples/               # Test datasets
│       ├── Text/              # Scam & safe CSV files
│       ├── Audio/             # Voice clone & normal MP3/WAV files
│       └── Video/             # Deepfake & normal MP4/image files
│
├── models/                    # Local AI model weights
└── run_local_tests.py         # Comprehensive test suite
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Node.js 18+
- ~2 GB RAM (CPU only, no GPU required)
- ~300 MB disk space for AI models

### 1. Install the SDK

```bash
cd sdk
pip install -e .
```

### 2. Start the Edge AI Server

```bash
cd app/edge_ai
uvicorn main:app --host 127.0.0.1 --port 8001
```

### 3. Start the Signaling Server

```bash
cd app/backend
npm install
node server.js
```

### 4. Start the Frontend

```bash
cd app/frontend
npm install
npm run dev
```

### 5. Cloud API (Optional)

```bash
cd cloud
pip install -r requirements.txt
cp .env.example .env
# Fill in API keys: LYZR_API_KEY, TAVILY_API_KEY, SWYTCHCODE_API_KEY
uvicorn app.main:app --reload --port 8000
```

---

## 🧪 Running Tests

Run the local edge testing suite (zero cloud escalation):

```bash
python run_local_tests.py
```

This tests all sample data across Text, Audio, Video, and Image gates, outputting:
- **Scam Probability** (0.0 to 1.0)
- **Latency** (milliseconds)

---

## 💻 SDK Usage

```python
from scamshield import ScamShield

shield = ScamShield(
    api_key="your-api-key",
    cloud_url="https://scamshield-sdk.onrender.com"
)

# Text scanning
result = await shield.scan_text("URGENT: Share OTP to unblock your account")
print(result.alert_level)     # "red"
print(result.explanation)     # Plain English explanation
print(result.recommendation)  # What the user should do

# Audio scanning
with open("suspicious_call.mp3", "rb") as f:
    result = await shield.scan_audio(f.read())

# Image scanning
with open("fake_receipt.png", "rb") as f:
    result = await shield.scan_image(f.read())

# Video scanning
with open("deepfake_call.mp4", "rb") as f:
    result = await shield.scan_video(f.read())
```

---

## 🧠 AI Gates — How They Work

### TextGate (CAHS-Gate V2)
- Encodes text using **all-MiniLM-L6-v2** sentence embeddings
- Computes cosine similarity against 4 intent anchor categories: `urgency`, `financial_ask`, `info_extraction`, `coercion`
- De-obfuscates leet-speak (`Shar3 y0ur 0TP` → `Share your OTP`)
- Translates Hinglish (`Aapka account block ho jayega` → `Your account will be blocked`)
- Applies dynamic trust scoring and stranger penalty

### AudioGate (DAVE Architecture)
- Transcribes speech using **Faster-Whisper** (CTranslate2)
- Analyses acoustic features with **Librosa**: MFCC variance, spectral flux, onset strength
- Detects AI voice clones (low MFCC variance = unnaturally consistent intonation)
- Pipes transcription through TextGate for semantic analysis
- Final score = `max(acoustic_score, text_score)`

### VideoGate
- Extracts frames using **OpenCV**
- Runs each frame through **ImageGate** (ELA + noise analysis)
- Tracks face movement using **MediaPipe** 468-point face mesh
- Extracts audio track via **FFmpeg** → pipes through AudioGate
- Final score = `max(frame_score, audio_score, face_jitter_score)`

### ImageGate
- Performs **Error Level Analysis (ELA)** to detect pixel-level manipulation
- Runs **FFT frequency analysis** to detect GAN/diffusion-generated textures
- Extracts text via **PyTesseract OCR** → pipes through TextGate
- Final score = `max(forensic_score, ocr_text_score)`

---

## 🤝 Cloud Partners

| Partner | Role |
|---------|------|
| **Render** | Cloud API hosting (Singapore) + PostgreSQL |
| **Lyzr AI** | Multi-agent fraud council (Audio Forensic, Social Engineering, Vision Forensic, Chief Fraud Officer) |
| **Tavily** | Real-time OSINT — checks URLs against live scam/phishing databases |
| **Swytchcode** | YAML-defined pipeline orchestration for modality routing |

---

## 🌐 Deployment

### Render (One-Click Blueprint)

The project includes a `cloud/render.yaml` blueprint that deploys:
- **scamshield-api** — Python Cloud API
- **scamshield-signaling** — Node.js WebSocket server
- **scamshield-frontend** — React static site
- **scamshield-db** — PostgreSQL database

```bash
# Push to GitHub, then in Render Dashboard:
# + New → Blueprint → Select repo → Apply
```

---

## 📊 Detection Thresholds

| Gate | Threshold | Scoring Method |
|------|-----------|----------------|
| TextGate | ≥ 0.55 | Intent similarity + URL penalty + stranger penalty − behavioral discount |
| AudioGate | ≥ 0.55 | max(acoustic anomaly, transcription intent) |
| VideoGate | ≥ 0.55 | max(frame forensics, audio track, face jitter) |
| ImageGate | ≥ 0.30 | max(ELA + noise forensics, OCR text intent) |

---

## 🔐 Privacy & Security

- **Raw content never leaves the device.** Only mathematical feature vectors (embeddings, MFCCs, ELA scores) are sent to the cloud.
- **PII Scrubber** strips all personally identifiable information before cloud transmission.
- **No microphone streaming to external servers.** Audio analysis happens locally via WebSocket to `localhost:8001`.
- **TRAI-compliant** SMS header parsing for Indian telecom standards.
- **Works fully offline** after initial model download.

---

## 📜 License

This project was built for **Smart India Hackathon (SIH) 2026 — Decode**.

---

## 👥 Team

Built by a team of 6 engineers covering AI/ML, Cloud Architecture, Frontend, Computer Vision, Data Engineering, and DevOps.

---

> **ScamShield: Protecting every call, message, and video — before the scam succeeds.**
