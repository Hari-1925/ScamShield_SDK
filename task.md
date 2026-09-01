# Text Gate V2 (CAHS-Gate) Implementation

- [ ] Create ContextEngine (SQLite) in sdk/scamshield/gate/context_engine.py to track contact history and trust scores.
- [ ] Implement PreProcessor in sdk/scamshield/gate/preprocessor.py for de-obfuscation and entity extraction.
- [ ] Refactor TextGate in sdk/scamshield/gate/text_gate.py:
  - [ ] Support contact_id parameter.
  - [ ] Implement Semantic Intent Classifier (4 axes).
  - [ ] Implement Historical RAG evaluator for High-Trust contacts.
- [ ] Update gent.py to parse and pass contact_id in /scan_local_text.
- [ ] Update App.jsx to pass contact_id when sending a text message for scanning.
- [ ] Verify test cases (Family OTP, Police Impersonation, etc.) work correctly.
