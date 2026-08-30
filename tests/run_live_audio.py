import asyncio
import io
import wave
import time
import pyaudio
from scamshield.client import ScamShield

# Audio config
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 1024

class LiveAudioTest:
    def __init__(self):
        self.shield = ScamShield(api_key="scamshield-dev-key", cloud_url="http://localhost:8000", timeout=45)
        self.audio_frames = []
        
    def audio_callback(self, in_data, frame_count, time_info, status):
        self.audio_frames.append(in_data)
        return (in_data, pyaudio.paContinue)

    async def run(self):
        print("Loading AI Models...")
        self.shield._ensure_models_loaded()
        stream = await self.shield.start_audio_stream()
        await stream.connect()
        
        # Initialize Audio
        p = pyaudio.PyAudio()
        audio_stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, 
                              input=True, frames_per_buffer=CHUNK,
                              stream_callback=self.audio_callback)
        
        audio_stream.start_stream()
        
        last_process_time = time.time()
        print("\n" + "="*50)
        print("🟢 LIVE AUDIO CALL STARTED")
        print("Speak into your microphone. Press Ctrl+C to quit.")
        print("="*50 + "\n")
        
        try:
            while True:
                if time.time() - last_process_time >= 3.0:
                    # Capture Audio
                    buf = io.BytesIO()
                    with wave.open(buf, 'wb') as wf:
                        wf.setnchannels(CHANNELS)
                        wf.setsampwidth(p.get_sample_size(FORMAT))
                        wf.setframerate(RATE)
                        wf.writeframes(b''.join(self.audio_frames))
                    wav_bytes = buf.getvalue()
                    self.audio_frames.clear()
                    
                    print("\nProcessing 3s chunk...")
                    res = await stream.send_chunk(wav_bytes)
                    
                    print(f"Transcript: {res.transcription}")
                    print(f"Threat Level: {res.running_score:.2f} | Alert Level: {res.alert_level.value.upper()}")
                    if res.should_alert:
                        print("[🚨 ALERT TRIGGERED] Proceed with caution!")
                        
                    if getattr(stream, 'cloud_verified_severe_threat', False):
                        print("\n[⛔ EXTREME THREAT DETECTED] Cloud AI has verified a severe scam in progress.")
                        print("[⛔ CALL AUTO-TERMINATED to protect user!]")
                        break
                        
                    last_process_time = time.time()
                
                await asyncio.sleep(0.1)
                
        except KeyboardInterrupt:
            print("\nStopping...")
        finally:
            audio_stream.stop_stream()
            audio_stream.close()
            p.terminate()
            
            final = await stream.close()
            print("\n=== FINAL CALL REPORT ===")
            print(f"Max Threat Level: {final.confidence_score}")
            print(f"Recommendation: {final.recommendation}")

if __name__ == "__main__":
    asyncio.run(LiveAudioTest().run())
