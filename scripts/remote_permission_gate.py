import sys
import json
import os
import datetime
from pathlib import Path
import httpx

PROJECT_ROOT = Path(r"C:\Users\PMLS\Documents\IDE Remote")
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

LOG_FILE = PROJECT_ROOT / "scripts" / "gate.log"

def log(msg: str):
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    except Exception:
        pass

def is_companion_mode_on() -> bool:
    try:
        resp = httpx.get("http://127.0.0.1:8765/manifest.json", timeout=1.0)
        return resp.status_code == 200
    except Exception:
        return False

def is_sensitive_file(file_path: str) -> bool:
    name = Path(file_path).name.lower()
    sensitive_names = [".env", "id_rsa", "id_ed25519", "credentials.json", "secret.json", "auth.json"]
    if any(name == s or name.startswith(s) for s in sensitive_names):
        return True
    sensitive_exts = [".pem", ".key", ".pfx", ".p12", ".pkcs12"]
    if any(name.endswith(ext) for ext in sensitive_exts):
        return True
    return False

def emit_user_progress(tool_name: str, args: dict):
    """Emits clean, high-level task progress for the end user on mobile (skips internal companion noise)."""
    try:
        label = ""
        is_code = False
        if tool_name == "read_file":
            raw_path = args.get("Path", "")
            fp = Path(raw_path).name
            if not fp or any(i in fp.lower() for i in ["gate.log", "session_allowed", "single_use", "mobile_listener", "run_companion", "config.json"]):
                return
            is_code = any(fp.endswith(ext) for ext in [".json", ".py", ".js", ".ts", ".html", ".css", ".md", ".env"])
            label = f"Analyzing {fp}"
        elif tool_name in ["write_file", "edit_file"]:
            raw_path = args.get("Path", "")
            fp = Path(raw_path).name
            if not fp or any(i in fp.lower() for i in ["gate.log", "session_allowed", "single_use", "config.json"]):
                return
            is_code = any(fp.endswith(ext) for ext in [".json", ".py", ".js", ".ts", ".html", ".css", ".md"])
            label = f"Modifying {fp}"
        elif tool_name == "run_command":
            cmd = args.get("CommandLine", "").strip()
            if any(i in cmd.lower() for i in ["mobile_listener", "run_companion", "gate.log", "run_gate", "netstat", "taskkill", "stop-process", "get-process", "get-content", "get-childitem", "git status", "git rev-parse", "git log"]):
                return
            summary = args.get("toolSummary", "")
            if summary and not any(i in summary.lower() for i in ["mobile", "companion", "gate", "status"]):
                label = f"Running {summary.lower()}"
            elif "python" in cmd.lower():
                parts = cmd.split()
                script = [p for p in parts if p.endswith(".py")]
                label = f"Running {Path(script[0]).name}" if script else "Running script"
            elif cmd.startswith("git"):
                parts = cmd.split()
                sub = parts[1] if len(parts) > 1 else ""
                label = f"Running git {sub}"
            else:
                label = "Running task"
        
        if label:
            httpx.post("http://127.0.0.1:8765/api/progress", json={
                "step_type": "tool_start",
                "label": label,
                "is_code": is_code,
                "detail": ""
            }, timeout=0.4)
    except Exception:
        pass

def main():
    try:
        raw_input = sys.stdin.read()
        if not raw_input:
            print(json.dumps({"decision": "allow"}))
            return

        payload = json.loads(raw_input)
        conv_id = payload.get("conversationId", "")
        tool_call = payload.get("toolCall", {})
        tool_name = tool_call.get("name", "")
        args = tool_call.get("args", {})

        # 1. MCP Tools for mobile-companion are always allowed
        if tool_name == "call_mcp_tool":
            server_name = args.get("ServerName", "")
            if "mobile-companion" in server_name:
                print(json.dumps({"decision": "allow"}))
                return

        # 2. Safe internal tools that never touch files or processes
        safe_tools = ["manage_task", "schedule", "read_resource", "list_resources", "search_marketplace"]
        if tool_name in safe_tools:
            print(json.dumps({"decision": "allow"}))
            return

        # 3. Check Companion Mode status
        companion_active = is_companion_mode_on()
        if not companion_active:
            log(f"Tool {tool_name} requested, but Companion Mode is OFF. Reverting to desktop review.")
            print(json.dumps({
                "decision": "ask",
                "reason": "Companion Mode is OFF. Standard desktop review active."
            }))
            return

        from src.antigravity_companion.permissions import (
            get_current_grants,
            is_granted_for_session,
            grant_allow_once,
            grant_allow_conversation,
            grant_allow_always,
            build_command_grant_variants,
            build_file_grant_variants
        )

        current_grants = get_current_grants()

        # Emit user-friendly progress to mobile
        emit_user_progress(tool_name, args)

        # 4. Handle File Access Tools (read_file, write_file, edit_file)
        if tool_name in ["read_file", "write_file", "edit_file"]:
            file_path = args.get("Path", "").strip()
            
            # Non-sensitive project files are auto-allowed silently
            if not is_sensitive_file(file_path):
                print(json.dumps({"decision": "allow"}))
                return

            # Check if this sensitive file is already granted
            file_variants = build_file_grant_variants(file_path)
            if any(v in current_grants for v in file_variants) or is_granted_for_session(conv_id, file_path, is_file=True):
                print(json.dumps({"decision": "allow"}))
                return

            # Route sensitive file request to MOBILE
            log(f"Routing sensitive file permission request to mobile: {file_path}")
            title_text = "Allow read access to this path?" if tool_name == "read_file" else "Allow access to this path?"
            options = [
                "1  Yes, allow this time",
                "2  Yes, and always allow in this conversation",
                "3  Yes, and always allow",
                "4  No (tell the agent what to do instead)"
            ]
            try:
                resp = httpx.post(
                    "http://127.0.0.1:8765/api/ask",
                    json={
                        "title": title_text,
                        "target": file_path,
                        "question": file_path,
                        "options": options,
                        "timeout": 300
                    },
                    timeout=310.0
                )
                if resp.status_code == 200:
                    raw_decision = resp.json().get("decision", "").strip()
                    lower_decision = raw_decision.lower()
                    if "timeout" in lower_decision:
                        print(json.dumps({"decision": "deny", "reason": "Timed out waiting for mobile approval."}))
                        return

                    if lower_decision.startswith("1") or "allow this time" in lower_decision:
                        grant_allow_once(file_path, is_file=True)
                        print(json.dumps({"decision": "allow"}))
                        return
                    elif lower_decision.startswith("2") or "conversation" in lower_decision:
                        grant_allow_conversation(conv_id, file_path, is_file=True)
                        print(json.dumps({"decision": "allow"}))
                        return
                    elif lower_decision.startswith("3") or "always allow" in lower_decision:
                        grant_allow_always(file_path, is_file=True)
                        print(json.dumps({"decision": "allow"}))
                        return
                    else:
                        print(json.dumps({"decision": "deny", "reason": f"File access denied on mobile ({raw_decision})"}))
                        return
            except Exception as e:
                log(f"Exception during file mobile ask: {e}")

            print(json.dumps({"decision": "deny", "reason": "Failed to reach mobile device for file permission."}))
            return

        # 5. Handle Terminal Commands (run_command)
        cmd = args.get("CommandLine", "").strip()

        # Auto-allow internal companion inspection commands silently
        companion_infra_patterns = [
            "mobile_listener.py", "run_companion.py", "pwa_bridge",
            "scripts/remote_permission_gate", "scripts/run_gate.bat", "scripts/run_post_tool.bat",
            "python.exe -c", "python -c", "Get-Content", "Get-ChildItem", "Select-String",
            "Test-Path", "Get-Item", "Get-Location", "Get-Process", "Stop-Process",
            "Get-CimInstance", "taskkill", "tasklist", "netstat", "curl", "git"
        ]
        if any(p.lower() in cmd.lower() for p in companion_infra_patterns):
            log(f"Auto-allowing companion infra command: {cmd[:60]}")
            grant_allow_once(cmd)
            print(json.dumps({"decision": "allow"}))
            return

        # Check if command is already granted
        cmd_variants = build_command_grant_variants(cmd)
        if any(v in current_grants for v in cmd_variants) or is_granted_for_session(conv_id, cmd):
            log(f"Command already granted: {cmd[:60]}")
            print(json.dumps({"decision": "allow"}))
            return

        # Route ungranted command to MOBILE PWA
        log(f"Routing permission request to mobile phone: {cmd[:80]}")
        short_cmd = cmd[:200] + "..." if len(cmd) > 200 else cmd
        options = [
            "1  Yes, allow this time",
            "2  Yes, and always allow in this conversation",
            "3  Yes, and always allow",
            "4  No (tell the agent what to do instead)"
        ]

        try:
            resp = httpx.post(
                "http://127.0.0.1:8765/api/ask",
                json={
                    "title": "Allow this command to run?",
                    "target": short_cmd,
                    "question": short_cmd,
                    "options": options,
                    "timeout": 300
                },
                timeout=310.0
            )
            if resp.status_code == 200:
                raw_decision = resp.json().get("decision", "").strip()
                log(f"Mobile user decision received: '{raw_decision}'")
                lower_decision = raw_decision.lower()

                if "timeout" in lower_decision:
                    print(json.dumps({"decision": "deny", "reason": "Permission request timed out waiting for mobile approval."}))
                    return

                if lower_decision.startswith("1") or "allow this time" in lower_decision:
                    grant_allow_once(cmd)
                    print(json.dumps({"decision": "allow"}))
                    return
                elif lower_decision.startswith("2") or "conversation" in lower_decision:
                    grant_allow_conversation(conv_id, cmd)
                    print(json.dumps({"decision": "allow"}))
                    return
                elif lower_decision.startswith("3") or "always allow" in lower_decision:
                    grant_allow_always(cmd)
                    print(json.dumps({"decision": "allow"}))
                    return
                else:
                    print(json.dumps({"decision": "deny", "reason": f"Execution was denied from mobile device ({raw_decision})"}))
                    return
        except Exception as e:
            log(f"Exception during mobile ask: {e}")

        print(json.dumps({"decision": "deny", "reason": "Execution timed out or failed to reach mobile device."}))

    except Exception as e:
        log(f"Fatal exception in gate: {e}")
        print(json.dumps({"decision": "allow"}))

if __name__ == "__main__":
    main()
