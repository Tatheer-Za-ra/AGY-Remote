import sys
import json
from pathlib import Path
import httpx

PROJECT_ROOT = Path(r"C:\Users\PMLS\Documents\IDE Remote")
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

def emit_progress(label: str):
    try:
        httpx.post("http://127.0.0.1:8765/api/progress", json={
            "step_type": "tool_done",
            "label": label,
            "detail": ""
        }, timeout=0.5)
    except Exception:
        pass

try:
    raw_input = sys.stdin.read()
    if raw_input:
        payload = json.loads(raw_input)
        tool_call = payload.get("toolCall", {})
        tool_name = tool_call.get("name", "")
        args = tool_call.get("args", {})
        
        label = ""
        if tool_name == "run_command":
            cmd = args.get("CommandLine", "").strip()
            # Ignore internal companion noise
            if not any(i in cmd.lower() for i in ["mobile_listener", "run_companion", "gate.log", "run_gate", "netstat", "taskkill", "stop-process", "get-process", "get-content", "get-childitem"]):
                if "python" in cmd.lower():
                    parts = cmd.split()
                    script = [p for p in parts if p.endswith(".py")]
                    label = f"Completed {Path(script[0]).name} >" if script else "Completed script >"
                elif cmd.startswith("git"):
                    parts = cmd.split()
                    sub = parts[1] if len(parts) > 1 else ""
                    label = f"Finished git {sub} >"
                else:
                    label = "Completed command >"

        elif tool_name in ["read_file", "write_file", "edit_file"]:
            fp = Path(args.get("Path", "")).name
            if fp and not any(i in fp.lower() for i in ["gate.log", "session_allowed", "single_use"]):
                action = "Analyzed" if tool_name == "read_file" else "Updated"
                label = f"{action} {fp} >"

        if label:
            emit_progress(label)
except Exception:
    pass

try:
    from src.antigravity_companion.permissions import cleanup_single_use
    cleanup_single_use()
except Exception:
    pass

print(json.dumps({}))
