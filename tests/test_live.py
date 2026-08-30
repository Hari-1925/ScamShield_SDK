import asyncio
import io
import wave
import time
from scamshield.client import ScamShield

async def simulate_live_call():
    shield = ScamShield("dev")
    print("Initializing Live Audio Stream...")
    
    # Preload models
    shield._ensure_models_loaded()
    
    stream = await shield.start_audio_stream()
    await stream.connect()
    
    # We will simulate a live call by reading an audio file in 3-second chunks
    filename = "tests/samples/irl_scam.mp3"
    print(f"\n[LIVE SIMULATION] Incoming call... (Simulating from {filename})")
    
    # Extract raw wav bytes to chunk easily using librosa
    import librosa
    import soundfile as sf
    
    audio, sr = librosa.load(filename, sr=16000)
    
    # 3 seconds per chunk
    chunk_size = 3 * sr 
    
    for i in range(0, len(audio), chunk_size):
        chunk_audio = audio[i:i+chunk_size]
        
        # Convert numpy array back to wav bytes
        buf = io.BytesIO()
        sf.write(buf, chunk_audio, sr, format='WAV', subtype='PCM_16')
        wav_bytes = buf.getvalue()
        
        start_t = time.time()
        result = await stream.send_chunk(wav_bytes)
        elapsed = time.time() - start_t
        
        print(f"\n[00:0{result.chunk_id*3}] Processing chunk took {elapsed:.2f}s")
        if result.transcription:
            print(f"Transcript: \"{result.transcription}\"")
            
        print(f"Threat Level: {result.running_score:.3f} | Alert Level: {result.alert_level.value}")
        
        if result.should_alert:
            print("[ALERT] HIGH THREAT DETECTED! Triggering UI Alert overlay...")
            
    final_result = await stream.close()
    print("\n[CALL ENDED] Final Call Report:")
    print(f"Max Threat Level: {final_result.confidence_score}")
    print(f"Recommendation: {final_result.recommendation}")

if __name__ == "__main__":
    asyncio.run(simulate_live_call())
