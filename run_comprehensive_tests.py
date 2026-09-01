import asyncio
from scamshield.gate.text_gate import TextGate
import json

def run_tests():
    gate = TextGate()
    gate.load()
    
    print("\n" + "="*50)
    print(" ScamShield CAHS-Gate V2 Comprehensive Test Suite")
    print("="*50 + "\n")
    
    # 1. Setup Context Profiles
    gate.context_engine.log_message("trusted_dad", "Hey son, how are you?", sender="them", is_saved=True)
    gate.context_engine.log_message("trusted_dad", "Can you send me some cash for groceries?", sender="them", is_saved=True)
    # Fast forward trust score for dad (simulate 50 messages)
    for _ in range(50): 
        gate.context_engine.log_message("trusted_dad", "normal message", sender="them", is_saved=True)
    gate.context_engine.log_message("trusted_dad", "hey what was the netflix pin again?", sender="them", is_saved=True)
    
    # Simulate a bank contact
    for _ in range(10): 
        gate.context_engine.log_message("bank_alert", "Account alert", sender="them", is_saved=True)

    tests = [
        # --- TRUE POSITIVES (Should be True) ---
        {"name": "Investment Scam", "text": "Double your money in 24 hours guaranteed. Invest now!", "contact": "stranger1", "saved": False, "expect": True},
        {"name": "OTP Extraction", "text": "Please share the 6-digit OTP sent to your phone to verify delivery.", "contact": "stranger2", "saved": False, "expect": True},
        {"name": "Lottery Scam", "text": "You have won 1 million dollars! Pay  registration fee to claim.", "contact": "stranger3", "saved": False, "expect": True},
        {"name": "KYC Phishing", "text": "Your bank KYC has expired. Update immediately or account will be blocked.", "contact": "stranger4", "saved": False, "expect": True},
        {"name": "Police Impersonation", "text": "This is the CBI. You are under investigation. Pay fine to avoid arrest.", "contact": "stranger5", "saved": False, "expect": True},
        {"name": "Job Scam with Fee", "text": "Work from home and earn 50k/month. Pay 999 registration fee.", "contact": "stranger6", "saved": False, "expect": True},
        {"name": "Stranded Foreigner", "text": "I am stuck at the airport, my card is blocked. Can you send me some money please?", "contact": "stranger7", "saved": False, "expect": True},
        {"name": "UPI Fraud", "text": "Scan this QR code or enter your UPI PIN to receive the cash back.", "contact": "stranger8", "saved": False, "expect": True},
        
        # --- TRUE NEGATIVES (Should be False) ---
        {"name": "Normal Casual Message", "text": "Hey, what are you doing this weekend?", "contact": "stranger9", "saved": False, "expect": False},
        {"name": "Legit Bank SMS", "text": "Dear Customer, Rs.500 has been debited from A/c XX1234. Available Bal: Rs.1000.", "contact": "bank_alert", "saved": True, "expect": False},
        {"name": "Family Money Request", "text": "Can you send the otp for the account?", "contact": "trusted_dad", "saved": True, "expect": False},
        {"name": "News Article About Scam", "text": "Police arrested a gang today for running a fake investment scam and asking for OTPs.", "contact": "stranger10", "saved": False, "expect": False},
        {"name": "Empty Message", "text": "", "contact": "stranger11", "saved": False, "expect": False},
        
        # --- EDGE CASES (Should be True) ---
        {"name": "Mixed Language (Hinglish)", "text": "Bhai jaldi otp bhej, urgent hai account block ho jayega.", "contact": "stranger12", "saved": False, "expect": True},
        {"name": "Obfuscated Keywords", "text": "p@y th3 f33 to unbl0ck y0ur acc0unt a.s.a.p", "contact": "stranger13", "saved": False, "expect": True},
    ]

    passed_count = 0
    for t in tests:
        res = gate.run(t["text"], contact_id=t["contact"], is_saved_contact=t["saved"])
        success = res.passed_gate == t["expect"]
        if success:
            passed_count += 1
            status = "? PASS"
        else:
            status = "? FAIL"
            
        print(f"{status} | {t['name']}")
        print(f"   Text: '{t['text']}'")
        print(f"   Result: Scam={res.passed_gate} (Expected={t['expect']})")
        print(f"   Reason: {res.gate_reason}\n")

    print("="*50)
    print(f" Test Summary: {passed_count}/{len(tests)} Tests Passed")
    print("="*50 + "\n")

run_tests()
