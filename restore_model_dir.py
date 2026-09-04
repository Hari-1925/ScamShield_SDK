with open('app/local_agent/agent.py', 'r', encoding='utf-8') as f:
    text = f.read()

import re
old_shield = r'shield = ScamShield\(\s*api_key=\"scamshield-dev-key-2026\",\s*cloud_url=\"https://scamshield-sdk.onrender.com\"\s*\)'
new_shield = '''shield = ScamShield(
    api_key="scamshield-dev-key-2026",
    cloud_url="https://scamshield-sdk.onrender.com",
    model_dir=os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "models"))
)'''

text = re.sub(old_shield, new_shield, text)
with open('app/local_agent/agent.py', 'w', encoding='utf-8') as f:
    f.write(text)
