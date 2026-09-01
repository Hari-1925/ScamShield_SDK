from scamshield.gate.text_gate import TextGate

tg = TextGate()
tg.load()

msgs = [
    "URGENT: Your SBI account will be blocked in 24 hours. Share OTP with our executive immediately to restore access: bit.ly/sbi-verify",
    "Congratulations! You won Rs 25 lakh in KBC Lucky Draw. Pay processing fee at bit.ly/kbc-claim-prize to receive your prize.",
    "Join our trading group. Guaranteed 40% returns per month. Zero risk. My cousin made Rs 2 lakh in 30 days. WhatsApp 9123456789.",
    "Your KYC has expired. Your HDFC account will be permanently blocked in 24 hours. Update immediately: tinyurl.com/hdfc-kyc-update",
    "This is CBI cybercrime department. An arrest warrant has been issued in your name. Pay Rs 15000 to settle this case. Call immediately.",
    "You are selected for a Data Entry job at TCS. Earn Rs 50,000/month from home. Pay Rs 2000 registration fee to confirm your seat.",
    "I am stuck at Mumbai airport. My wallet was stolen. I have feelings for you. Please transfer Rs 5000. I will pay you back double when I reach home.",
    "You have received Rs 50000 cashback on your UPI. Enter your UPI PIN to claim the amount before it expires in 1 hour."
]

print('\nTesting as UNKNOWN contact (trust=0.1):')
for m in msgs:
    res = tg.run(m, contact_id='unknown', is_saved_contact=False)
    print(f'[{res.passed_gate}] {res.gate_score:.2f} | {m[:30]}...')

print('\nTesting as SAVED contact (trust=0.5):')
for m in msgs:
    res = tg.run(m, contact_id='friend1', is_saved_contact=True)
    print(f'[{res.passed_gate}] {res.gate_score:.2f} | {m[:30]}...')

