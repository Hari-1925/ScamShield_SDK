from scamshield.gate.text_gate import TextGate
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

gate = TextGate()
gate.load()

gate.context_engine.log_message("mitigation_test", "hey what was the netflix pin again?", sender="them", is_saved=True)
for _ in range(5): gate.context_engine.log_message("mitigation_test", "normal message", sender="them", is_saved=True)

# Actually let's look at EXACTLY what gets fetched
res = gate.run("Can you send the otp for the account?", contact_id="mitigation_test", is_saved_contact=True)
print("Is Scam?", res.passed_gate)
print("Mitigated?", res.vectors.get("context_mitigated"))
print("History Fetched:", gate.context_engine.get_recent_messages("mitigation_test", limit=5))

e1 = gate.model.encode(["Can you send the otp for the account?"])[0]
e2 = gate.model.encode(["hey what was the netflix pin again?"])[0]
print("Similarity:", cosine_similarity([e1], [e2])[0][0])
