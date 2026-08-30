import asyncio
import io
import cv2
import sounddevice as sd
from scipy.io.wavfile import write
from scamshield import ScamShield

async def run_live_video_test():
    print("\n" + "="*50)
    print("📹 INITIALIZING SCAMSHIELD LIVE WEBCAM TEST")
    print("="*50)
    
    # 1. Start up SDK Video Stream
    shield = ScamShield(api_key="test_key")
    stream = await shield.start_video_stream()
    
    fs = 16000  # 16kHz for Whisper
    chunk_duration = 4  # Record 4 seconds of audio per chunk
    
    # 2. Initialize Webcam
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Error: Could not open your webcam.")
        return

    print("\n✅ System Ready (Webcam & Mic Active)!")
    print("Listening & Watching... (Try saying scam phrases into your camera!)")
    print("Press Ctrl+C to stop.\n")
    
    try:
        while True:
            # Step A: Capture a single video frame from the webcam
            ret, frame = cap.read()
            frame_bytes = b""
            if ret:
                # Convert the OpenCV frame to JPEG bytes
                _, buffer = cv2.imencode('.jpg', frame)
                frame_bytes = buffer.tobytes()

            # Step B: Record 4 seconds of audio from the microphone
            recording = sd.rec(int(chunk_duration * fs), samplerate=fs, channels=1, dtype='int16')
            sd.wait()
            
            wav_io = io.BytesIO()
            write(wav_io, fs, recording)
            audio_bytes = wav_io.getvalue()
            
            # Step C: Feed BOTH frame and audio to the SDK Video Stream
            result = await stream.send_frame(frame_bytes=frame_bytes, audio_bytes=audio_bytes)
            
            # Print the results
            print("-" * 50)
            face_status = "👤 Face Detected" if stream.face_detected else "👻 No Face Detected"
            print(f"📷  Visual: {face_status}")
            print(f"🗣️   Audio: '{result.transcription.strip()}'")
            print(f"📊  Danger Score: {result.running_score:.3f}")
            
            if result.should_alert:
                print("\n🚨🚨🚨 WEBCAM SCAM DETECTED! 🚨🚨🚨")
                print("The system has triggered a video escalation alert!\n")
                
    except KeyboardInterrupt:
        print("\nStopping live monitor...")
    finally:
        cap.release()
        await stream.close()

if __name__ == "__main__":
    asyncio.run(run_live_video_test())
