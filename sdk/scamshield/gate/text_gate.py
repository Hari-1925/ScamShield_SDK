import re
import numpy as np
from typing import Dict, Any
from scamshield.models import GateResult
from scamshield.gate.patterns import SCAM_PATTERNS, HIGH_RISK_KEYWORDS, SUSPICIOUS_URL_PATTERNS

class TextGate:
    MODEL = "all-MiniLM-L6-v2"

    def __init__(self, model_dir: str = None):
        self.model_dir = model_dir
        self.model = None
        self.pattern_matrix = None
        self.pattern_labels = []

    def load(self):
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as e:
            print(f"ImportError loading sentence-transformers: {e}")
            print("Please install sentence-transformers: pip install sentence-transformers scikit-learn")
            return

        model_name_or_path = self.MODEL
        import os
        if self.model_dir:
            local_path = os.path.join(self.model_dir, "all-MiniLM-L6-v2")
            if os.path.exists(local_path):
                model_name_or_path = local_path
                
        self.model = SentenceTransformer(model_name_or_path)
        
        # Pre-compute embeddings
        all_patterns = []
        for category, patterns in SCAM_PATTERNS.items():
            for p in patterns:
                all_patterns.append(p)
                self.pattern_labels.append(category)
                
        self.pattern_matrix = self.model.encode(all_patterns)
        print("Text gate loaded")

    def run(self, text: str) -> GateResult:
        if self.model is None or self.pattern_matrix is None:
            raise RuntimeError("TextGate not loaded. Call load() first.")

        if not text.strip():
            return GateResult(
                passed_gate=False, gate_score=0.0, gate_reason="Empty text",
                vectors={"embedding": [], "keyword_hits": [], "url_flags": [], "extracted_urls": [], "scam_category": "none"},
                modality="text"
            )

        text_lower = text.lower()
        
        # Step 1 - Keyword scan
        matched_keywords = [kw for kw in HIGH_RISK_KEYWORDS if kw in text_lower]
        hits = len(matched_keywords)
        keyword_score = min(hits * 0.08, 0.40)

        # Step 2 - URL pattern check
        matched_url_patterns = [pat for pat in SUSPICIOUS_URL_PATTERNS if pat in text_lower]
        matches = len(matched_url_patterns)
        url_score = min(matches * 0.15, 0.45)
        
        url_regex = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        extracted_urls = re.findall(url_regex, text)

        # Step 3 - Semantic embedding
        embedding = self.model.encode([text])[0]
        
        from sklearn.metrics.pairwise import cosine_similarity
        similarities = cosine_similarity([embedding], self.pattern_matrix)[0]
        top_idx = np.argmax(similarities)
        top_score = float(similarities[top_idx])
        top_category = self.pattern_labels[top_idx]
        
        semantic_score = max(0.0, (top_score - 0.25) / 0.75)

        # Step 4 - Fuse
        # Use a capped sum instead of weighted average so that strong semantic 
        # matches don't get suppressed if there are no URLs (like in audio/images)
        gate_score = min(semantic_score + keyword_score + url_score, 1.0)
        
        # Step 5 - Decision
        threshold = 0.30
        passed = gate_score >= threshold
        
        # Determine highest trigger
        scores = {"semantic": semantic_score, "keyword": keyword_score, "url": url_score}
        gate_reason = max(scores, key=scores.get)
        
        # Privacy Layer: If this is flagged as a scam (passed == True), we scrub the raw text
        # before returning it in the vectors so the Cloud never receives PII.
        from scamshield.privacy.scrubber import PIIScrubber
        scrubber = PIIScrubber()
        
        # We save the scrubbed text in the vectors payload so the API can use it
        scrubbed_text = scrubber.scrub(text) if passed else ""

        return GateResult(
            passed_gate=passed,
            gate_score=float(gate_score),
            gate_reason=f"Highest trigger: {gate_reason}",
            vectors={
                "embedding": embedding.tolist(),
                "keyword_hits": matched_keywords,
                "url_flags": matched_url_patterns,
                "extracted_urls": extracted_urls,
                "scam_category": top_category,
                "scrubbed_transcription": scrubbed_text
            },
            modality="text"
        )
