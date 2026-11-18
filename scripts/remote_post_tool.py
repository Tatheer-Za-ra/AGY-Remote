import sys
import json
import os
from pathlib import Path
import httpx

PROJECT_ROOT = Path(os.environ.get("PLUGIN_ROOT") or Path(__file__).resolve().parent.parent)
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

def emit_progress(label: str, is_code: bool = False):
    try:
        httpx.post("http://127.0.0.1:8765/api/progress", json={
            "step_type": "tool_done",
            "label": label,
            "is_code": is_code,
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
        is_code = False
        if tool_name == "run_command":
            cmd = args.get("CommandLine", "").strip()
            # Ignore internal companion noise
            if not any(i in cmd.lower() for i in ["mobile_listener", "run_companion", "shutdown_companion", "gate.log", "run_gate", "netstat", "taskkill", "stop-process", "get-process", "get-content", "get-childitem", "git status", "git rev-parse", "git log"]):
                summary = args.get("toolSummary", "")
                if summary and not any(i in summary.lower() for i in ["mobile", "companion", "gate", "status"]):
                    label = f"Ran {summary.lower()} >"
                elif "python" in cmd.lower():
                    parts = cmd.split()
                    script = [p for p in parts if p.endswith(".py")]
                    label = f"Ran {Path(script[0]).name} >" if script else "Ran script >"
                elif cmd.startswith("git"):
                    parts = cmd.split()
                    sub = parts[1] if len(parts) > 1 else ""
                    label = f"Ran git {sub} >"
                else:
                    label = "Ran command >"

        elif tool_name == "read_file":
            raw_path = args.get("Path", "")
            fp = Path(raw_path).name
            if fp and not any(i in fp.lower() for i in ["gate.log", "session_allowed", "single_use", "config.json", "mobile_listener", "run_companion", "shutdown_companion"]):
                is_code = any(fp.endswith(ext) for ext in [".json", ".py", ".js", ".ts", ".html", ".css", ".md", ".env"])
                start_line = args.get("StartLine")
                end_line = args.get("EndLine")
                lines_tag = f" #L{start_line}-{end_line}" if start_line and end_line else ""
                label = f"Analyzed {fp}{lines_tag}"

        elif tool_name in ["write_file", "edit_file"]:
            raw_path = args.get("Path", "")
            fp = Path(raw_path).name
            if fp and not any(i in fp.lower() for i in ["gate.log", "session_allowed", "single_use", "config.json", "mobile_listener", "run_companion", "shutdown_companion"]):
                is_code = any(fp.endswith(ext) for ext in [".json", ".py", ".js", ".ts", ".html", ".css", ".md"])
                label = f"Modified {fp}"

        if label:
            emit_progress(label, is_code=is_code)
except Exception:
    pass

try:
    from src.antigravity_companion.permissions import cleanup_single_use
    cleanup_single_use()
except Exception:
    pass

print(json.dumps({}))
