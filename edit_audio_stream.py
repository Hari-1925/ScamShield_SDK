with open('sdk/scamshield/streaming/audio_stream.py', 'r', encoding='utf-8') as f:
    text = f.read()

import re

# Update threshold
text = text.replace('self.threshold = 0.30', 'self.threshold = 0.55')

# Replace the cloud escalation block with local explainer
old_block = r"if self\.cloud_client and not getattr\(self, '_is_escalating', False\) and not self\.cloud_verified_severe_threat:.*?asyncio\.create_task\(_bg_escalate\(\)\)"
new_block = '''if not getattr(self, '_is_escalating', False) and not self.cloud_verified_severe_threat:
                self._is_escalating = True
                
                async def _bg_escalate():
                    try:
                        print("\\n[?? LOCAL ESCALATION] Generating Local LLM Explanation...\\n")
                        from scamshield.explainers.local_llm import explainer_instance
                        
                        # Generate explanation locally!
                        # This runs synchronously, so we wrap it in an executor to avoid blocking the asyncio loop
                        loop = asyncio.get_event_loop()
                        explanation_text = await loop.run_in_executor(
                            None, 
                            explainer_instance.explain, 
                            audio_vectors, 
                            self.running_score
                        )
                        
                        self.cloud_verified_severe_threat = True
                        
                        print(f"\\n[?? LOCAL VERDICT GENERATED]\\n")
                        
                        if self.event_queue:
                            await self.event_queue.put({
                                "action": "CLOUD_VERDICT", # Keep the same action name so the React UI understands it, but it's local now
                                "explanation": explanation_text,
                                "is_scam": True,
                                "score": self.running_score
                            })
                            
                    except Exception as e:
                        import traceback
                        traceback.print_exc()
                        print(f"[Local Escalation Failed] {repr(e)}")
                    finally:
                        self._is_escalating = False
                
                asyncio.create_task(_bg_escalate())'''

text = re.sub(old_block, new_block, text, flags=re.DOTALL)

with open('sdk/scamshield/streaming/audio_stream.py', 'w', encoding='utf-8') as f:
    f.write(text)
