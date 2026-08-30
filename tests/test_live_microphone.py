import asyncio
import io
import sounddevice as sd
from scipy.io.wavfile import write
from scamshield import ScamShield

async def run_live_test():
    print("\n" + "="*50)
    print("🎤 INITIALIZING SCAMSHIELD LIVE MICROPHONE TEST")
    print("="*50)
    
    # 1. Start up SDK
    shield = ScamShield(api_key="test_key")
    stream = await shield.start_audio_stream()
    
    fs = 16000  # 16kHz is perfect for Whisper
    chunk_duration = 4  # Record 4 seconds at a time
    
    print("\n✅ System Ready!")
    print("Listening... (Try saying things like 'I need you to transfer rupees' or 'police arrest')")
    print("Press Ctrl+C to stop.\n")
    
    try:
        while True:
            # 2. Record 4 seconds of audio from the microphone
            recording = sd.rec(int(chunk_duration * fs), samplerate=fs, channels=1, dtype='int16')
            sd.wait()  # Wait until recording is finished
            
            # 3. Convert raw audio array into WAV bytes in memory
            wav_io = io.BytesIO()
            write(wav_io, fs, recording)
            audio_bytes = wav_io.getvalue()
            
            # 4. Feed the live chunk to the SDK!
            result = await stream.send_chunk(audio_bytes)
            
            # 5. Print the results
            print("-" * 40)
            print(f"🗣️  You said: '{result.transcription.strip()}'")
            print(f"📊  Danger Score: {result.running_score:.3f}")
            
            if result.should_alert:
                print("\n🚨🚨🚨 SCAM DETECTED! 🚨🚨🚨")
                print("The system has triggered an escalation alert!\n")
                
    except KeyboardInterrupt:
        print("\nStopping live monitor...")
    finally:
        await stream.close()

if __name__ == "__main__":
    asyncio.run(run_live_test())
