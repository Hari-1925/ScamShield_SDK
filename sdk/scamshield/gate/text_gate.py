import re
import numpy as np
from typing import Dict, Any
from scamshield.models import GateResult
from scamshield.gate.preprocessor import PreProcessor
from scamshield.gate.context_engine import ContextEngine

class TextGate:
    # Use the same lightweight model as before, but evaluate on Intents
    MODEL = "all-MiniLM-L6-v2"

    INTENT_ANCHORS = {
        "urgency": [
            "urgent action required", "your account will be blocked", "do this immediately", 
            "hurry up", "do it fast", "action needed now"
        ],
        "financial_ask": [
            "send me the money", "transfer funds to this account", "pay the customs fee", 
            "can you lend me cash", "paytm me", "upi transfer", "pay the registration fee",
            "send money for tickets", "i am stranded need cash", "invest now", 
            "double your money", "guaranteed returns", "job registration fee",
            "pickpocketed", "send me money to return home", "lost my phone need money"
        ],
        "info_extraction": [
            "share the otp", "what is your password", "tell me the verification code", 
            "confirm your account details", "kyc update", "send the pin", "enter your upi pin",
            "scan this qr code"
        ],
        "coercion": [
            "this is the police", "you are under arrest", "we will take legal action", 
            "customs officer warning", "cbi investigation", "court order"
        ]
    }

    def __init__(self, model_dir: str = None):
        self.model_dir = model_dir
        self.model = None
        self.intent_matrix = None
        self.intent_labels = []
        self.context_engine = ContextEngine()

    def load(self):
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as e:
            print(f"ImportError loading sentence-transformers: {e}")
            return

        model_name_or_path = self.MODEL
        import os
        if self.model_dir:
            local_path = os.path.join(self.model_dir, "all-MiniLM-L6-v2")
            if os.path.exists(local_path):
                model_name_or_path = local_path
                
        self.model = SentenceTransformer(model_name_or_path)
        
        # Pre-compute intent anchors
        all_anchors = []
        for intent, anchors in self.INTENT_ANCHORS.items():
            for a in anchors:
                all_anchors.append(a)
                self.intent_labels.append(intent)
                
        self.intent_matrix = self.model.encode(all_anchors)
        print("Text gate loaded (CAHS-Gate V2)")

    def run(self, text: str, contact_id: str = "unknown", is_saved_contact: bool = False, sender: str = "them") -> GateResult:
        if self.model is None or self.intent_matrix is None:
            raise RuntimeError("TextGate not loaded. Call load() first.")

        if not text.strip():
            return GateResult(
                passed_gate=False, gate_score=0.0, gate_reason="Empty text",
                vectors={"embedding": [], "scam_category": "none"}, modality="text"
            )

        # 1. Log message to Context Engine and fetch Trust Score
        self.context_engine.log_message(contact_id, text, sender=sender, is_saved=is_saved_contact)
        trust_score = self.context_engine.get_trust_score(contact_id)

        # 2. Pre-process (De-obfuscate & Extract Entities)
        clean_text = PreProcessor.deobfuscate(text)
        entities = PreProcessor.extract_entities(text)
        
        # Base url heuristic
        url_score = min(len(entities["urls"]) * 0.20, 0.40)

        # 3. Semantic Intent Evaluation
        embedding = self.model.encode([clean_text])[0]
        from sklearn.metrics.pairwise import cosine_similarity
        similarities = cosine_similarity([embedding], self.intent_matrix)[0]
        
        # Aggregate scores by intent
        intent_scores = {intent: 0.0 for intent in self.INTENT_ANCHORS.keys()}
        for i, score in enumerate(similarities):
            label = self.intent_labels[i]
            intent_scores[label] = max(intent_scores[label], float(score))

        top_intent = max(intent_scores, key=intent_scores.get)
        top_intent_score = intent_scores[top_intent]
        
        # 4. Generalized Behavioral Trust Scoring
        # Instead of arbitrary penalties and similarity hacks, we modulate the threat
        # based on continuous Trust and Behavioral Deviation.
        
        historical_intent_baseline = 0.0
        is_context_mitigated = False
        
        if trust_score > 0.3:
            history = self.context_engine.get_recent_messages(contact_id, limit=5)
            past_scores = []
            for past_msg in history[1:]:
                if not past_msg.strip(): continue
                past_emb = self.model.encode([past_msg])[0]
                past_sims = cosine_similarity([past_emb], self.intent_matrix)[0]
                
                # Aggregate past scores by intent (same as we do for the current message)
                past_intent_scores = {intent: 0.0 for intent in self.INTENT_ANCHORS.keys()}
                for i, score in enumerate(past_sims):
                    label = self.intent_labels[i]
                    past_intent_scores[label] = max(past_intent_scores[label], float(score))
                
                # Look specifically at their historical score for the CURRENT active intent
                past_scores.append(past_intent_scores[top_intent])
                
            if past_scores:
                historical_intent_baseline = float(max(past_scores))
                if top_intent_score - historical_intent_baseline < 0.10:
                    is_context_mitigated = True
                    
        # Unified Mathematical Equation (No magic case-by-case if statements)
        # 1. Base Threat: How suspicious is the text natively? (0.2 to 0.8 usually)
        # 2. URL Penalty: Adds flat risk if URLs are present
        # 3. Stranger Penalty: Low trust dynamically increases the risk surface
        # 4. Behavioral Discount: If they historically talk like this, it reduces risk
        
        stranger_penalty = (1.0 - trust_score) * 0.25
        behavioral_discount = historical_intent_baseline * trust_score
        
        gate_score = top_intent_score + url_score + stranger_penalty - behavioral_discount
        gate_score = max(0.0, min(gate_score, 1.0))

        # 5. Decision
        passed = gate_score >= 0.55
        
        reason = "Safe"
        if passed:
            if is_context_mitigated:
                reason = f"Mitigated by Context. Intent: {top_intent} ({top_intent_score:.2f})"
            else:
                reason = f"Intent: {top_intent} ({top_intent_score:.2f}). Trust: {trust_score:.2f}. Mitigated: {is_context_mitigated}"
        
        from scamshield.privacy.scrubber import PIIScrubber
        scrubber = PIIScrubber()
        scrubbed_text = scrubber.scrub(text) if passed else ""

        return GateResult(
            passed_gate=passed,
            gate_score=float(gate_score),
            gate_reason=reason,
            vectors={
                "embedding": embedding.tolist(),
                "intents": intent_scores,
                "entities": entities,
                "scam_category": top_intent,
                "scrubbed_transcription": scrubbed_text,
                "trust_score": trust_score,
                "context_mitigated": is_context_mitigated,
                # Backward compatibility for V1 Cloud API
                "keyword_hits": [top_intent] if passed else [],
                "url_flags": [],
                "extracted_urls": entities["urls"]
            },
            modality="text"
        )
