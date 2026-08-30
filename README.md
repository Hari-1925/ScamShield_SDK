# ScamShield

Multimodal scam and deepfake detection SDK
for social media platforms.

Protects users from: UPI fraud, OTP scams,
bank phishing, AI voice cloning, deepfake
video calls, and manipulated images.

## Architecture

Two-stage detection:
- Stage 1: Local gate (on device, 0ms network)
- Stage 2: Cloud brain (Render, vectors only)

Raw content never leaves the device.

## Cloud Partners

| Partner     | Role                          |
|-------------|-------------------------------|
| Render      | Cloud API hosting + PostgreSQL|
| Swytchcode  | AI pipeline orchestration     |
| Tavily      | Live threat intelligence      |
| Lyzr AI     | Deep analysis agents          |
| Gemini      | Fusion and explanation        |

## Setup

### 1. Cloud API (Render)

cd cloud
pip install -r requirements.txt
cp .env.example .env
# Fill in all API keys in .env
uvicorn app.main:app --reload --port 8000

### 2. SDK (local install)

cd sdk
pip install -e .

### 3. Swytchcode Pipeline

Install Swytchcode CLI:
  npm install -g @swytchcode/cli
  swytchcode login
  swytchcode deploy cloud/swytchcode/pipeline.yaml

### 4. Run Tests

# With cloud API running:
python tests/test_sdk.py
python tests/test_cloud.py

## Demo

from scamshield import ScamShield

shield = ScamShield(
    api_key="your-api-key",
    cloud_url="https://your-app.onrender.com"
)

result = await shield.scan_text(
    "URGENT: Share OTP to unblock account"
)
print(result.alert_level)    # red
print(result.explanation)    # plain English
print(result.recommendation) # what to do
