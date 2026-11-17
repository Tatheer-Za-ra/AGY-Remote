import atexit
import signal
import sys
import uvicorn
import logging
from src.antigravity_companion.config import config
from src.antigravity_companion.web_server import app
from src.antigravity_companion.tunnel import start_tunnel
from src.antigravity_companion.pwa_bridge import bridge
from src.antigravity_companion.permissions import setup_companion_grants, revert_companion_grants

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("companion_daemon")

def cleanup():
    logger.info("Cleaning up Companion Mode grants before shutdown...")
    revert_companion_grants()

atexit.register(cleanup)

def signal_handler(sig, frame):
    cleanup()
    sys.exit(0)

try:
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
except Exception:
    pass

def main():
    logger.info("Starting Antigravity Mobile Companion Daemon...")
    # 1. Setup automatic permissions for companion infrastructure
    setup_companion_grants()

    # 2. Start Ngrok / LAN tunnel
    local_url, public_url = start_tunnel(config.port)
    bridge.public_url = public_url or local_url

    print("=" * 60, flush=True)
    print("  📱 Antigravity Mobile Companion Daemon Active!", flush=True)
    print("=" * 60, flush=True)
    if public_url:
        print(f"  🌐 Remote (4G/5G): {public_url}", flush=True)
    print(f"  🏠 Local Wi-Fi:   {local_url}", flush=True)
    print("=" * 60, flush=True)

    try:
        uvicorn.run(app, host="0.0.0.0", port=config.port, log_level="warning")
    finally:
        cleanup()

if __name__ == "__main__":
    main()
