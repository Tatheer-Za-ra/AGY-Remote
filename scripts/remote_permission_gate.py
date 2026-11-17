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
            question_text = f"Allow access to sensitive file on Desktop?\n\nPath: {file_path}"
            options = [
                "1. Yes, allow this time",
                "2. Yes, and always allow in this conversation",
                "3. Yes, and always allow",
                "4. No (deny access)"
            ]
            try:
                resp = httpx.post(
                    "http://127.0.0.1:8765/api/ask",
                    json={"question": question_text, "options": options, "timeout": 300},
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
            "Get-CimInstance", "taskkill", "tasklist", "netstat", "curl", "git status",
            "git config", "git diff", "git log", "git rev-parse"
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
        short_cmd = cmd[:160] + "..." if len(cmd) > 160 else cmd
        question_text = f"Allow command execution on Desktop?\n\n{short_cmd}"
        options = [
            "1. Yes, allow this time",
            "2. Yes, and always allow in this conversation",
            "3. Yes, and always allow",
            "4. No (deny execution)"
        ]

        try:
            resp = httpx.post(
                "http://127.0.0.1:8765/api/ask",
                json={"question": question_text, "options": options, "timeout": 300},
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
