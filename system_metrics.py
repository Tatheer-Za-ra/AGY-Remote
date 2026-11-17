import time
import datetime
import sys
import platform
import httpx
import os
import psutil

API_URL = "http://127.0.0.1:8765/api/notify"

def push_mobile(title: str, message: str, code: str = None):
    try:
        httpx.post(API_URL, json={"title": title, "message": message, "code": code}, timeout=3.0)
    except Exception:
        pass

def check_heartbeat_status():
    for p in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = p.info.get('cmdline') or []
            cmd_str = " ".join(cmdline).lower()
            if "heartbeat_test.py" in cmd_str:
                return True, p.info['pid']
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return False, None

def get_system_snapshot():
    cpu = psutil.cpu_percent(interval=None)
    vm = psutil.virtual_memory()
    is_hb, hb_pid = check_heartbeat_status()
    hb_str = f"RUNNING (PID: {hb_pid})" if is_hb else "TERMINATED (Inactive)"
    task_count = 2 if is_hb else 1
    
    details = (
        f"CPU: {cpu:.1f}% | RAM: {vm.percent:.1f}% ({vm.used/(1024**3):.1f}/{vm.total/(1024**3):.1f} GB)\n"
        f"Heartbeat Script: {hb_str}\n"
        f"Active Monitored Tasks: {task_count} ({'Heartbeat + Metrics' if is_hb else 'Metrics Only'})"
    )
    return is_hb, details

print("=" * 60, flush=True)
print("  📊 Antigravity System Metrics Monitor (Dynamic Detection)", flush=True)
print(f"  🖥️ Host: {platform.node()} | Platform: {platform.platform()}", flush=True)
print("=" * 60, flush=True)

# Initial push on start with real detection
_, initial_details = get_system_snapshot()
push_mobile(
    "📊 System Monitor Resumed (Corrected)",
    "Dynamic task detection active. Heartbeat status verified.",
    initial_details
)

count = 1
try:
    while True:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        is_hb, details = get_system_snapshot()
        log_line = f"[{now}] 📊 Monitor #{count:04d} | HB: {'ALIVE' if is_hb else 'DEAD'} | CPU: {psutil.cpu_percent():.1f}%"
        print(log_line, flush=True)

        # Push to mobile every 15 iterations (~45 seconds)
        if count % 15 == 0:
            push_mobile(
                f"📊 System Metrics #{count:04d}",
                f"Desktop resource monitoring active at {now}.",
                details
            )

        count += 1
        time.sleep(3)
except KeyboardInterrupt:
    push_mobile("🛑 System Monitor Stopped", "system_metrics.py was stopped by user.")
    print("\n[!] System metrics process stopped gracefully.", flush=True)
