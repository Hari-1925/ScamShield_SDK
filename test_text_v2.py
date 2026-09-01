import asyncio
from scamshield.gate.text_gate import TextGate
import json

gate = TextGate()
gate.load()

print("\n--- Test 1: Dad asking for OTP ---")
for _ in range(50): gate.context_engine.log_message("dad123", "normal message", sender="them", is_saved=True)
gate.context_engine.log_message("dad123", "hey can you send me the netflix otp?", sender="them", is_saved=True)
res1 = gate.run("what is the otp?", contact_id="dad123", is_saved_contact=True)
print("Is Scam?", res1.passed_gate, "Reason:", res1.gate_reason)
