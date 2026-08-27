import re
import numpy as np
from typing import Dict, Any
from scamshield.models import GateResult
from scamshield.gate.patterns import SCAM_PATTERNS, HIGH_RISK_KEYWORDS, SUSPICIOUS_URL_PATTERNS

class TextGate:
    MODEL = "all-MiniLM-L6-v2"

    def __init__(self):
        self.model = None
        self.pattern_matrix = None
        self.pattern_labels = []

    def load(self):
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            print("Please install sentence-transformers: pip install sentence-transformers scikit-learn")
            return

        self.model = SentenceTransformer(self.MODEL)
        
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
        
        semantic_score = max(0.0, (top_score - 0.35) / 0.65)

        # Step 4 - Fuse
        gate_score = (semantic_score * 0.60) + (keyword_score * 0.25) + (url_score * 0.15)
        
        # Step 5 - Decision
        threshold = 0.35
        passed = gate_score >= threshold
        
        # Determine highest trigger
        scores = {"semantic": semantic_score * 0.60, "keyword": keyword_score * 0.25, "url": url_score * 0.15}
        gate_reason = max(scores, key=scores.get)

        return GateResult(
            passed_gate=passed,
            gate_score=float(gate_score),
            gate_reason=f"Highest trigger: {gate_reason}",
            vectors={
                "embedding": embedding.tolist(),
                "keyword_hits": matched_keywords,
                "url_flags": matched_url_patterns,
                "extracted_urls": extracted_urls,
                "scam_category": top_category
            },
            modality="text"
        )
