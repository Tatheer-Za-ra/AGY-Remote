import httpx

resp = httpx.post("http://127.0.0.1:8765/api/notify", json={
    "title": "✅ File Modified: heartbeat_test.py",
    "message": "I updated heartbeat_test.py with system host info and formatted mobile companion heartbeats as you requested!",
    "code": "print(f'[{now}] Heartbeat #{count:04d} | Status: Healthy | Mobile Companion Synced')"
})
print("Notification sent:", resp.json())

