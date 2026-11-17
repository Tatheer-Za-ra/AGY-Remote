import httpx
import sys

prompt_context = sys.argv[1] if len(sys.argv) > 1 else "I am in mobile companion mode! Type your instruction on your phone and tap Send."
print(f"Entering Mobile Companion Mode...\nPrompt: {prompt_context}\nWaiting for mobile input from phone...", flush=True)

try:
    resp = httpx.post("http://127.0.0.1:8765/api/remote_turn", json={
        "prompt_context": prompt_context,
        "timeout": 180
    }, timeout=190)
    data = resp.json()
    instruction = data.get("instruction", "")
    print(f"\n=========================================")
    print(f"  📥 INSTRUCTION RECEIVED FROM MOBILE:")
    print(f"  '{instruction}'")
    print(f"=========================================")
except Exception as e:
    print("Error waiting for mobile input:", e)

