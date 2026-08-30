import re

class PIIScrubber:
    def __init__(self):
        # Regex patterns for fast edge-based PII scrubbing
        self.patterns = {
            "EMAIL": r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+',
            "PHONE": r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
            "CREDIT_CARD": r'(?:\d[ -]*?){13,16}',
            "SSN": r'\b\d{3}[- ]?\d{2}[- ]?\d{4}\b',
            # Basic fallback for capitalized names (John Doe). Not perfect, but lightweight for Edge.
            "NAME": r'\b[A-Z][a-z]+\s[A-Z][a-z]+\b'
        }

    def scrub(self, text: str) -> str:
        """
        Replaces matched PII in the text with generic brackets like [PHONE].
        """
        if not text:
            return text
            
        scrubbed_text = text
        for pii_type, pattern in self.patterns.items():
            scrubbed_text = re.sub(pattern, f"[{pii_type}]", scrubbed_text)
            
        return scrubbed_text
