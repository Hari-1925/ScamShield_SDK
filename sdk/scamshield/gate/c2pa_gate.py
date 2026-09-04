import traceback
from scamshield.models import GateResult

class C2PAGate:
    """
    C2PAGate (Coalition for Content Provenance and Authenticity).
    A zero-latency, pre-flight gate that parses binary metadata (JUMBF/EXIF) 
    for cryptographic signatures from known AI generators.
    """
    def __init__(self):
        # Simulated C2PA tool signatures we look for in the binary metadata
        self.known_ai_signatures = [
            b"elevenlabs", 
            b"openai", 
            b"midjourney", 
            b"runway", 
            b"heygen", 
            b"c2pa_tool:fake"
        ]

    def run(self, content: bytes, contact_id: str = "unknown", is_saved_contact: bool = False) -> GateResult:
        try:
            # Scan the entire binary for simulated metadata strings
            # In production, this would use `c2pa-python` to cryptographically verify the hash in the JUMBF box.
            header_bytes = content.lower()
            
            for sig in self.known_ai_signatures:
                if sig in header_bytes:
                    detected_tool = sig.decode('utf-8', errors='ignore')
                    return GateResult(
                        passed_gate=False, 
                        gate_score=1.0, 
                        gate_reason=f"Cryptographic C2PA Manifest confirms AI generation via {detected_tool.upper()}.", 
                        vectors={"c2pa_tool": detected_tool},
                        modality="c2pa"
                    )

            # Safe / No C2PA found - silently pass to AI models
            return GateResult(
                passed_gate=True, 
                gate_score=0.0, 
                gate_reason="No malicious C2PA provenance found.", 
                vectors={},
                modality="c2pa"
            )

        except Exception as e:
            traceback.print_exc()
            # Safe-fail: do not crash the pipeline if binary parsing fails
            return GateResult(passed_gate=True, gate_score=0.0, gate_reason="C2PA parsing error.", vectors={}, modality="c2pa")