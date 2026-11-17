import sys
import time
import httpx
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

def main():
    print("Initiating clean Companion Mode shutdown...")

    # 1. Notify mobile PWA of intentional shutdown
    try:
        resp = httpx.post("http://127.0.0.1:8765/api/shutdown", json={
            "message": "Remote companion session has ended cleanly. Desktop permissions have reverted to standard review."
        }, timeout=2.0)
        print("✅ Disconnect event broadcasted to mobile PWA.")
        time.sleep(0.6)  # Allow WebSocket frame delivery before killing process
    except Exception as e:
        print(f"Warning: Could not notify daemon: {e}")

    # 2. Revert config.json grants
    try:
        from src.antigravity_companion.permissions import revert_companion_grants
        revert_companion_grants()
        print("✅ Desktop permissions restored in config.json.")
    except Exception as e:
        print(f"Error reverting grants: {e}")

    # 3. Clean active marker
    try:
        marker = PROJECT_ROOT / ".companion_active"
        if marker.exists():
            marker.unlink(missing_ok=True)
            print("✅ Removed .companion_active marker.")
    except Exception:
        pass

    print("Companion Mode shutdown completed successfully.")

if __name__ == "__main__":
    main()
