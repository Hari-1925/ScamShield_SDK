import asyncio
import io
import wave
import time
import soundfile as sf
import numpy as np
from scamshield.streaming.audio_stream import AudioStreamClient
from scamshield.client import ScamShield

async def mock_live_stream():
    shield = ScamShield(api_key="dev", cloud_url="http://localhost:8000")
    client = AudioStreamClient(shield.audio_gate, shield.cloud)
    
    print("Loading test audio...")
    # Load 10 seconds of irl_scam.mp3
    audio, sr = sf.read("tests/samples/irl_scam.mp3")
    audio = audio[:sr*10] # 10 seconds
    
    # Process in 3-second chunks like the live mic
    chunk_samples = sr * 3
    
    for i in range(0, len(audio), chunk_samples):
        chunk_data = audio[i:i+chunk_samples]
        if len(chunk_data) == 0:
            break
            
        # Convert to 16-bit PCM for WAV
        pcm16 = (chunk_data * 32767).astype(np.int16)
        
        buf = io.BytesIO()
        with wave.open(buf, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sr)
            wf.writeframes(pcm16.tobytes())
            
        wav_bytes = buf.getvalue()
        
        print(f"\n--- Sending Chunk {i//chunk_samples + 1} ---")
        res = await client.send_chunk(wav_bytes)
        print(f"Transcript out: {res.transcription}")
        await asyncio.sleep(0.1)

if __name__ == "__main__":
    asyncio.run(mock_live_stream())
