import asyncio
import io
import wave
import time
import cv2
import pyaudio
from scamshield.client import ScamShield

# Audio config
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 1024

class LiveWebcamTest:
    def __init__(self):
        self.shield = ScamShield(api_key="scamshield-dev-key", cloud_url="http://localhost:8000", timeout=45)
        self.audio_frames = []
        self.latest_threat_level = 0.0
        self.latest_alert = "none"
        self.latest_transcript = ""
        
    def audio_callback(self, in_data, frame_count, time_info, status):
        """Runs in a background thread by PyAudio to continuously fetch mic data"""
        self.audio_frames.append(in_data)
        return (in_data, pyaudio.paContinue)

    async def process_chunk(self, stream, frame_bytes, wav_bytes):
        """Runs the AI models asynchronously without freezing the video feed"""
        res = await stream.send_frame(frame_bytes, wav_bytes)
        self.latest_threat_level = res.running_score
        self.latest_alert = res.alert_level.value if res.alert_level else "none"
        if res.transcription:
            # Keep transcript short for display
            self.latest_transcript = res.transcription[:60] + "..."
        print(f"[SDK] Processed 3s chunk. Threat: {res.running_score:.2f} | Alert: {self.latest_alert}")

    async def run(self):
        print("Loading AI Models...")
        self.shield._ensure_models_loaded()
        stream = await self.shield.start_video_stream()
        await stream.connect()
        
        # Initialize Audio
        p = pyaudio.PyAudio()
        audio_stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, 
                              input=True, frames_per_buffer=CHUNK,
                              stream_callback=self.audio_callback)
        
        # Initialize Video
        cap = cv2.VideoCapture(0)
        audio_stream.start_stream()
        
        last_process_time = time.time()
        print("\n" + "="*50)
        print("🟢 LIVE STREAMING STARTED")
        print("Look into the camera and speak. Press 'q' to quit.")
        print("="*50 + "\n")
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    print("Failed to grab camera frame.")
                    break
                    
                # --- 1. Overlay current threat status on the video feed ---
                color = (0, 255, 0) # Green (BGR format)
                if self.latest_alert == "orange":
                    color = (0, 165, 255) # Orange
                elif self.latest_alert == "red":
                    color = (0, 0, 255) # Red
                    
                cv2.putText(frame, f"Threat: {self.latest_threat_level:.2f}", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 3)
                cv2.putText(frame, f"Alert: {self.latest_alert.upper()}", (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 3)
                cv2.putText(frame, f"Text: {self.latest_transcript}", (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                
                cv2.imshow('Live ScamShield Video Call', frame)
                
                # --- 2. Every 3 seconds, send a chunk to the SDK ---
                if time.time() - last_process_time >= 3.0:
                    # Capture current visual frame
                    _, img_encoded = cv2.imencode('.jpg', frame)
                    frame_bytes = img_encoded.tobytes()
                    
                    # Capture accumulated audio
                    buf = io.BytesIO()
                    with wave.open(buf, 'wb') as wf:
                        wf.setnchannels(CHANNELS)
                        wf.setsampwidth(p.get_sample_size(FORMAT))
                        wf.setframerate(RATE)
                        wf.writeframes(b''.join(self.audio_frames))
                    wav_bytes = buf.getvalue()
                    self.audio_frames.clear()
                    
                    # Run SDK processing in background so video doesn't freeze
                    asyncio.create_task(self.process_chunk(stream, frame_bytes, wav_bytes))
                    
                    last_process_time = time.time()
                
                # --- 3. Break if user presses 'q' ---
                # WaitKey must be called frequently to refresh the OpenCV window
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                    
                # --- 4. Auto Terminate if Extreme Threat Verified by Cloud ---
                if getattr(stream, 'cloud_verified_severe_threat', False):
                    print("\n[⛔ EXTREME THREAT DETECTED] Cloud AI has verified a severe scam in progress.")
                    print("[⛔ CALL AUTO-TERMINATED to protect user!]")
                    # Show one last frame with the termination warning
                    cv2.putText(frame, "CALL TERMINATED FOR YOUR SAFETY", (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 4)
                    cv2.imshow('Live ScamShield Video Call', frame)
                    cv2.waitKey(2000)
                    break
                    
                # Allow asyncio tasks to run (crucial for create_task to execute)
                await asyncio.sleep(0.01)
        except asyncio.CancelledError:
            pass
        except KeyboardInterrupt:
            print("\nStopping...")
                
        # Cleanup
        print("Cleaning up...")
        audio_stream.stop_stream()
        audio_stream.close()
        p.terminate()
        cap.release()
        cv2.destroyAllWindows()
        
        final = await stream.close()
        print("\n=== FINAL CALL REPORT ===")
        print(f"Max Threat Level: {final.confidence_score}")
        print(f"Recommendation: {final.recommendation}")

if __name__ == "__main__":
    asyncio.run(LiveWebcamTest().run())
