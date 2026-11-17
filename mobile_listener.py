import httpx
import sys

# Silent background listener: waits up to 2 hours for mobile instruction
try:
    resp = httpx.post("http://127.0.0.1:8765/api/remote_turn", json={
        "prompt_context": "",
        "timeout": 7200
    }, timeout=7210)
    data = resp.json()
    instruction = data.get("instruction", "").strip()
    if instruction:
        print(f"\n=========================================")
        print(f"  📥 MOBILE PROMPT RECEIVED:")
        print(f"  {instruction}")
        print(f"=========================================")
    else:
        print("MOBILE_LISTENER_EMPTY")
except Exception as e:
    print(f"MOBILE_LISTENER_ERROR: {e}")

