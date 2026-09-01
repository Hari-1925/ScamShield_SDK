import re

with open('../sdk/scamshield/streaming/video_stream.py', 'r') as f:
    code = f.read()

# Replace audio_gate.run
old_audio = "gate_res = self.video_gate.audio_gate.run(audio_bytes, context_history=context)"
new_audio = "loop = asyncio.get_event_loop()\n        gate_res = await loop.run_in_executor(None, self.video_gate.audio_gate.run, audio_bytes, 'unknown', context)"
code = code.replace(old_audio, new_audio)

# Replace image_gate.run
old_image = "frame_res = self.video_gate.image_gate.run(frame_bytes, skip_ocr=True)"
new_image = "frame_res = await loop.run_in_executor(None, lambda: self.video_gate.image_gate.run(frame_bytes, skip_ocr=True))"
code = code.replace(old_image, new_image)

with open('../sdk/scamshield/streaming/video_stream.py', 'w') as f:
    f.write(code)
print("Fixed video_stream.py")
