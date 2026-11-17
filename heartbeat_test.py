import time
import datetime
import sys
import platform
import httpx

API_URL = "http://127.0.0.1:8765/api/notify"

def push_mobile(title: str, message: str, code: str = None):
    try:
        httpx.post(API_URL, json={"title": title, "message": message, "code": code}, timeout=3.0)
    except Exception:
        pass

print("=" * 60, flush=True)
print("  🚀 Antigravity Heartbeat Monitor — Live Mobile Sync", flush=True)
print(f"  🖥️ Host: {platform.node()} ({platform.system()} {platform.release()})", flush=True)
print("=" * 60, flush=True)

push_mobile(
    "🚀 Heartbeat Process Started",
    "Continuous desktop background execution is now running. Monitoring is active on your phone.",
    f"Host: {platform.node()} | PID: Active"
)

count = 1
try:
    while True:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        msg = f"[{now}] ❤️ Heartbeat #{count:04d} | Status: Healthy | Desktop IDE Active"
        print(msg, flush=True)

        # Push status update card to mobile every 10 iterations (30 seconds)
        if count % 10 == 0:
            push_mobile(
                f"❤️ Live Heartbeat #{count:04d}",
                f"Desktop session is continuously running in the background. System healthy at {now}.",
                f"Iterations: {count} | Host: {platform.node()}"
            )

        count += 1
        time.sleep(3)
except KeyboardInterrupt:
    push_mobile("🛑 Heartbeat Process Stopped", "The background task was terminated by the user.")
    print("\n[!] Heartbeat process stopped gracefully by user.", flush=True)
