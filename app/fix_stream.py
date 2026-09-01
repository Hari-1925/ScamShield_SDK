with open('../sdk/scamshield/streaming/audio_stream.py', 'r') as f:
    code = f.read()

old_call = "gate_res = self.audio_gate.run(audio_bytes, contact_id=self.contact_id)"
new_call = "loop = asyncio.get_event_loop()\n        gate_res = await loop.run_in_executor(None, self.audio_gate.run, audio_bytes, self.contact_id)"

code = code.replace(old_call, new_call)

with open('../sdk/scamshield/streaming/audio_stream.py', 'w') as f:
    f.write(code)
print("Fixed audio_stream.py")
