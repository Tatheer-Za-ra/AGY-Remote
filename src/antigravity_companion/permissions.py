import json
import logging
import os
import re
import shutil
from pathlib import Path
from typing import List, Optional, Set

logger = logging.getLogger("antigravity_companion.permissions")

CONFIG_PATH = Path.home() / ".gemini" / "config" / "config.json"
WORKSPACE_DIR = Path(os.environ.get("PLUGIN_ROOT") or os.getcwd())
SESSION_FILE = WORKSPACE_DIR / ".session_allowed.json"
SINGLE_USE_FILE = WORKSPACE_DIR / ".single_use_allowed.json"
BACKUP_FILE = WORKSPACE_DIR / ".config_backup.json"

COMPANION_DEFAULT_GRANTS = [
    "command(.\\.venv\\Scripts\\python.exe mobile_listener.py)",
    "command(.\\.venv\\Scripts\\python.exe run_companion.py)",
    "command(python mobile_listener.py)",
    "command(python run_companion.py)",
    "command(python3 mobile_listener.py)",
    "command(python3 run_companion.py)",
    "command(Get-Process *)",
    "command(Stop-Process *)",
    "command(taskkill *)",
    "command(netstat *)",
    "command(curl *)",
    "mcp(mobile-companion/*)",
    "mcp(mobile-companion/mobile_notify)",
    "mcp(mobile-companion/mobile_ask)",
    "mcp(mobile-companion/mobile_remote_turn)",
]

def _read_config() -> dict:
    if not CONFIG_PATH.exists():
        return {}
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error reading config.json: {e}")
        return {}

def _write_config(data: dict):
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.error(f"Error writing config.json: {e}")

def get_current_grants() -> List[str]:
    data = _read_config()
    return data.get("userSettings", {}).get("globalPermissionGrants", {}).get("allow", [])

def add_grants(grants: List[str]):
    if not grants:
        return
    data = _read_config()
    user_settings = data.setdefault("userSettings", {})
    perm_grants = user_settings.setdefault("globalPermissionGrants", {})
    allow_list = perm_grants.setdefault("allow", [])
    
    modified = False
    for g in grants:
        if g not in allow_list:
            allow_list.append(g)
            modified = True
            
    if modified:
        _write_config(data)
        logger.info(f"Added grants to config.json: {grants}")

def remove_grants(grants: List[str]):
    if not grants:
        return
    data = _read_config()
    allow_list = data.get("userSettings", {}).get("globalPermissionGrants", {}).get("allow", [])
    
    modified = False
    for g in grants:
        if g in allow_list:
            allow_list.remove(g)
            modified = True
            
    if modified:
        _write_config(data)
        logger.info(f"Removed grants from config.json: {grants}")

def setup_companion_grants():
    """Called when Companion Mode starts: backups config and injects companion grants."""
    try:
        if CONFIG_PATH.exists() and not BACKUP_FILE.exists():
            shutil.copy2(CONFIG_PATH, BACKUP_FILE)
            logger.info("Created backup of config.json before enabling Companion Mode.")
        add_grants(COMPANION_DEFAULT_GRANTS)
    except Exception as e:
        logger.error(f"Error in setup_companion_grants: {e}")

def revert_companion_grants():
    """Called when Companion Mode stops: restores clean grants."""
    try:
        remove_grants(COMPANION_DEFAULT_GRANTS)
        if SINGLE_USE_FILE.exists():
            SINGLE_USE_FILE.unlink(missing_ok=True)
        if SESSION_FILE.exists():
            SESSION_FILE.unlink(missing_ok=True)
        if BACKUP_FILE.exists():
            BACKUP_FILE.unlink(missing_ok=True)
        logger.info("Successfully reverted Companion Mode grants.")
    except Exception as e:
        logger.error(f"Error in revert_companion_grants: {e}")

def build_command_grant_variants(cmd: str) -> List[str]:
    """Generates grant string variants for terminal commands."""
    variants = []
    clean = cmd.strip().replace("\r\n", " ").replace("\n", " ")
    if not clean:
        return variants
    
    candidates = {clean}
    candidates.add(clean.replace("/", "\\"))
    candidates.add(clean.replace("\\", "/"))
    
    unquoted = clean.strip('"').strip("'")
    if unquoted != clean:
        candidates.add(unquoted)
        candidates.add(unquoted.replace("/", "\\"))
        candidates.add(unquoted.replace("\\", "/"))
        
    if ".venv" in clean.lower():
        venv_match = re.sub(r'^[.\/\\]*\.venv[\/\\]Scripts[\/\\]', '', clean, flags=re.IGNORECASE)
        if venv_match != clean:
            candidates.add(venv_match)
            candidates.add(venv_match.replace("/", "\\"))
            candidates.add(venv_match.replace("\\", "/"))

    for c in candidates:
        if c:
            g = f"command({c})"
            if g not in variants:
                variants.append(g)
                
    return variants

def build_file_grant_variants(file_path: str) -> List[str]:
    """Generates grant string variants for sensitive file access (e.g. .env)."""
    variants = []
    clean = file_path.strip()
    if not clean:
        return variants
        
    candidates = {
        clean,
        clean.replace("\\", "/"),
        clean.replace("/", "\\"),
        clean.lower(),
        clean.replace("\\", "/").lower(),
        clean.replace("/", "\\").lower()
    }
    
    for c in candidates:
        if c:
            g = f"file({c})"
            if g not in variants:
                variants.append(g)
                
    return variants

def grant_allow_once(item: str, is_file: bool = False):
    """Registers a command or file grant for single execution and marks it for cleanup."""
    variants = build_file_grant_variants(item) if is_file else build_command_grant_variants(item)
    add_grants(variants)
    try:
        pending = []
        if SINGLE_USE_FILE.exists():
            with open(SINGLE_USE_FILE, "r", encoding="utf-8") as f:
                pending = json.load(f).get("pending", [])
        for v in variants:
            if v not in pending:
                pending.append(v)
        with open(SINGLE_USE_FILE, "w", encoding="utf-8") as f:
            json.dump({"pending": pending}, f, indent=2)
    except Exception as e:
        logger.error(f"Error recording single use grant: {e}")

def cleanup_single_use():
    """Removes single-use grants after tool completion."""
    if not SINGLE_USE_FILE.exists():
        return
    try:
        with open(SINGLE_USE_FILE, "r", encoding="utf-8") as f:
            pending = json.load(f).get("pending", [])
        if pending:
            remove_grants(pending)
            SINGLE_USE_FILE.unlink(missing_ok=True)
            logger.info(f"Cleaned up {len(pending)} single-use grant(s).")
    except Exception as e:
        logger.error(f"Error cleaning up single use grants: {e}")

def grant_allow_conversation(conv_id: str, item: str, is_file: bool = False):
    """Grants command or file for this conversation session."""
    variants = build_file_grant_variants(item) if is_file else build_command_grant_variants(item)
    add_grants(variants)
    try:
        sessions = {}
        if SESSION_FILE.exists():
            with open(SESSION_FILE, "r", encoding="utf-8") as f:
                sessions = json.load(f).get("sessions", {})
        session_cmds = sessions.setdefault(conv_id, [])
        for v in variants:
            if v not in session_cmds:
                session_cmds.append(v)
        with open(SESSION_FILE, "w", encoding="utf-8") as f:
            json.dump({"sessions": sessions}, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving session grant: {e}")

def is_granted_for_session(conv_id: str, item: str, is_file: bool = False) -> bool:
    if not SESSION_FILE.exists():
        return False
    try:
        with open(SESSION_FILE, "r", encoding="utf-8") as f:
            sessions = json.load(f).get("sessions", {})
        session_cmds = sessions.get(conv_id, [])
        variants = build_file_grant_variants(item) if is_file else build_command_grant_variants(item)
        return any(v in session_cmds for v in variants)
    except Exception:
        return False

def grant_allow_always(item: str, is_file: bool = False):
    """Permanently adds command or file grant to config.json."""
    variants = build_file_grant_variants(item) if is_file else build_command_grant_variants(item)
    add_grants(variants)
