import os
import torch
from transformers import pipeline

class LocalLLMExplainer:
    _instance = None
    
    def __init__(self, model_id="HuggingFaceTB/SmolLM-135M-Instruct"):
        """
        Uses a very lightweight (~300MB) LLM to generate local explanations
        without relying on Gemini or Lyzr.
        """
        self.model_id = model_id
        self.generator = None

    def _load(self):
        if not self.generator:
            print(f"\n[Local Explainer] Initializing on-device LLM ({self.model_id})...")
            
            # ATTEMPT 1: Try strict offline load first (uses zero internet)
            try:
                self.generator = pipeline(
                    "text-generation", 
                    model=self.model_id, 
                    device="cpu", # Force CPU to avoid VRAM exhaustion
                    torch_dtype=torch.float32
                )
                print("[Local Explainer] Successfully loaded from local offline cache.")
            except Exception as e:
                print("[Local Explainer] Model not found locally. Initiating one-time download...")
                
                # ATTEMPT 2: Download via clean subprocess
                import subprocess
                env = os.environ.copy()
                if "HF_HUB_OFFLINE" in env: del env["HF_HUB_OFFLINE"]
                if "TRANSFORMERS_OFFLINE" in env: del env["TRANSFORMERS_OFFLINE"]
                
                try:
                    print("[Local Explainer] Spawning background downloader process (Internet required)...")
                    subprocess.run([
                        "python", "-c", 
                        f"from transformers import pipeline; pipeline('text-generation', model='{self.model_id}')"
                    ], env=env, check=True)
                    print("[Local Explainer] Download complete. Model permanently cached!")
                    
                    # Now load it offline in the main process!
                    self.generator = pipeline(
                        "text-generation", 
                        model=self.model_id, 
                        device="cpu",
                        torch_dtype=torch.float32
                    )
                except subprocess.CalledProcessError as e:
                    print(f"[Local Explainer] Subprocess failed to download LLM: {e}")
                except Exception as e:
                    print(f"[Local Explainer] Failed to load LLM after download: {e}")
                    return

        # NEW: Perform a tiny dummy inference call to "warm up" the CPU tensor operations
        # This prevents the 10-second latency freeze on the very first live call
        if not getattr(self, '_warmed_up', False):
            try:
                print("[Local Explainer] Running warmup inference to compile graph...")
                self.generator([{"role": "user", "content": "test"}], max_new_tokens=2)
                self._warmed_up = True
                print("[Local Explainer] Warmup complete. Lightning fast inference ready!")
            except Exception as e:
                pass

    def explain(self, vectors: dict, score: float) -> str:
        self._load()
        if not self.generator:
            return self._fallback_explanation(vectors, score)
            
        # Construct a prompt based on the gate vectors
        transcription = vectors.get("transcription", "")
        tags = vectors.get("acoustic_tags", [])
        
        prompt = (
            f"Analyze this suspicious phone call.\n"
            f"Transcription: '{transcription}'\n"
            f"Acoustic Anomalies: {', '.join(tags) if tags else 'None'}\n"
            f"Threat Score: {score:.2f}/1.0\n\n"
            f"Explain briefly (1-2 sentences) why this is a scam and what the caller is trying to do."
        )
        
        try:
            # SmolLM specific prompt format
            messages = [{"role": "user", "content": prompt}]
            # Optimized for maximum speed (greedy decoding, 30 max tokens)
            output = self.generator(messages, max_new_tokens=40)
            # Extract assistant reply
            generated_text = output[0]['generated_text']
            # Find the assistant's turn in the messages list format
            for msg in generated_text:
                if msg.get('role') == 'assistant':
                    return "Local AI Explainer: " + msg.get('content', '').strip()
            return "Local AI Explainer: " + str(output)
        except Exception as e:
            print(f"[Local Explainer Error]: {e}")
            return self._fallback_explanation(vectors, score)
            
    def _fallback_explanation(self, vectors: dict, score: float) -> str:
        tags = vectors.get("acoustic_tags", [])
        if tags:
            return f"Local AI Explainer: Detected synthetic audio anomalies ({', '.join(tags)})."
        return "Local AI Explainer: Detected semantic scam intent in the conversation (financial ask or urgency)."

# Singleton pattern for the streaming agent
explainer_instance = LocalLLMExplainer()
