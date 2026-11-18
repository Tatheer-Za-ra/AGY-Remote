import sys
import time
import httpx
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

def main():
    is_full_kill = any(arg in sys.argv for arg in ["--kill", "--full", "--stop"])
    
    if is_full_kill:
        print("Initiating full Companion Mode daemon shutdown...")
    else:
        print("Putting Companion Mode into Standby (desktop review restored, tunnel stays alive)...")

    # 1. Notify mobile PWA of standby / shutdown
    try:
        endpoint = "http://127.0.0.1:8765/api/companion/standby" if not is_full_kill else "http://127.0.0.1:8765/api/shutdown"
        resp = httpx.post(endpoint, json={
            "message": "Companion Mode is now in Standby. Desktop permissions have reverted to standard review."
        }, timeout=2.0)
        print("✅ Standby state broadcasted to mobile PWA.")
        time.sleep(0.3)
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

    if is_full_kill:
        print("Full Companion Mode shutdown completed successfully.")
    else:
        print("Companion Mode is in Standby. Desktop review restored. Mobile wakeup is ready.")

if __name__ == "__main__":
    main()
