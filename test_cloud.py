import asyncio
from scamshield.cloud.client import CloudClient
from scamshield.cloud.endpoints import CloudEndpoints

async def main():
    client = CloudClient("scamshield-dev-key-2026", "https://scamshield-sdk.onrender.com", timeout=180)
    audio_vectors = {
        "mfcc_mean": [0.0] * 40,
        "mfcc_std": [0.0] * 40,
        "zcr": 0.0,
        "spectral_centroid": 0.0,
        "pitch_std": 0.0,
        "energy_std": 0.0,
        "acoustic_tags": [],
        "transcription": "I am a scammer give me your money",
        "scrubbed_transcription": "I am a scammer give me your money",
        "keyword_hits": [],
        "gate_score": 0.9
    }
    try:
        res = await client.detect(CloudEndpoints.DETECT_AUDIO, audio_vectors, 0.9)
        print("Success:", res)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print("Error:", repr(e))

asyncio.run(main())
