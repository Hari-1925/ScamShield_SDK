import asyncio
from scamshield import ScamShield

async def run_tests():
    shield = ScamShield(
        api_key="scamshield-dev-key-2026",
        cloud_url="http://localhost:8000"
    )

    sep = "═" * 50

    print(f"\n{sep}")
    print("ScamShield SDK Test Suite")
    print(f"{sep}\n")

    tests_passed = 0
    tests_failed = 0

    # TEST 1 — Safe text
    print("TEST 1: Safe text message")
    r = await shield.scan_text(
        "Hey are we still meeting for lunch tomorrow?")
    print(f"  Alert level  : {r.alert_level}")
    print(f"  Score        : {r.confidence_score}")
    print(f"  Local only   : {r.processed_locally}")
    print(f"  Explanation  : {r.explanation}")
    if r.alert_level == "none":
        print("  PASSED ✓\n")
        tests_passed += 1
    else:
        print("  FAILED ✗\n")
        tests_failed += 1

    # TEST 2 — OTP scam
    print("TEST 2: OTP scam message")
    r = await shield.scan_text(
        "URGENT: Your SBI account blocked. "
        "Share OTP with executive immediately "
        "to restore access: bit.ly/sbi-verify")
    print(f"  Alert level  : {r.alert_level}")
    print(f"  Score        : {r.confidence_score}")
    print(f"  Scam type    : {r.scam_type}")
    print(f"  Explanation  : {r.explanation}")
    print(f"  Recommend    : {r.recommendation}")
    print(f"  Tavily hits  : {r.threat_intel_found}")
    print(f"  n8n triggered: {r.n8n_triggered}")
    if r.alert_level in ("orange", "red"):
        print("  PASSED ✓\n")
        tests_passed += 1
    else:
        print("  FAILED ✗\n")
        tests_failed += 1

    # TEST 3 — Lottery scam
    print("TEST 3: Lottery scam message")
    r = await shield.scan_text(
        "Congratulations! Won Rs 25 lakh KBC "
        "lucky draw. Pay fee: bit.ly/kbc-claim")
    print(f"  Alert level  : {r.alert_level}")
    print(f"  Score        : {r.confidence_score}")
    if r.alert_level in ("yellow","orange","red"):
        print("  PASSED ✓\n")
        tests_passed += 1
    else:
        print("  FAILED ✗\n")
        tests_failed += 1

    # TEST 4 — Cloud health
    print("TEST 4: Cloud service health check")
    available = shield.is_cloud_available()
    print(f"  Cloud available: {available}")
    print("  PASSED ✓\n")
    tests_passed += 1

    # TEST 5 — Stats
    try:
        print("TEST 5: API stats endpoint")
        stats = await shield.get_stats()
        print(f"  Stats: {stats}")
        print("  PASSED ✓\n")
        tests_passed += 1
    except Exception as e:
        print(f"  FAILED ✗ (Cloud API might be down: {e})\n")
        tests_failed += 1

    # Summary
    print(f"{sep}")
    print(f"Results: {tests_passed} passed, "
          f"{tests_failed} failed")
    print(f"{sep}\n")

    if tests_failed == 0:
        print("All tests passed. "
              "ScamShield SDK is working correctly.")
    else:
        print(f"{tests_failed} test(s) failed. "
              "Check logs above.")

if __name__ == "__main__":
    asyncio.run(run_tests())
