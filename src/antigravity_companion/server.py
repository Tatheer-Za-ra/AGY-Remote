import asyncio
import logging
import httpx
from typing import List, Optional

try:
    from mcp.server.mcpserver import MCPServer as FastMCP
except ImportError:
    from mcp.server.fastmcp import FastMCP

from .config import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("antigravity_companion.server")

mcp = FastMCP(
    "mobile-companion",
    instructions="Mobile companion PWA for Antigravity IDE: notify user, ask for approvals with buttons, and receive remote instructions."
)

BASE_URL = f"http://127.0.0.1:{config.port}"

@mcp.tool()
async def mobile_notify(title: str, message: str, code: Optional[str] = None) -> str:
    """
    Sends an instant push notification card to the user's mobile phone PWA.
    Use this to alert the user when a long task completes, when a build passes/fails,
    or to send code summaries while the user is away from their desk.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{BASE_URL}/api/notify",
                json={"title": title, "message": message, "code": code}
            )
            resp.raise_for_status()
            return "✅ Notification delivered to user's mobile phone."
    except Exception as e:
        logger.error(f"Failed to deliver notification to daemon: {e}")
        return f"❌ Failed to deliver notification: {str(e)}"

@mcp.tool()
async def mobile_ask(
    question: str,
    options: List[str] = ["Approve", "Deny"],
    timeout_seconds: int = 300
) -> str:
    """
    Asks the user an interactive question with clickable touch buttons on their mobile phone
    and pauses execution until the user taps an option or the timeout expires.
    Use this for approving terminal commands, file changes, git operations, or design decisions.
    """
    try:
        async with httpx.AsyncClient(timeout=float(timeout_seconds + 15)) as client:
            resp = await client.post(
                f"{BASE_URL}/api/ask",
                json={"question": question, "options": options, "timeout": timeout_seconds}
            )
            resp.raise_for_status()
            decision = resp.json().get("decision", "No response")
            return f"User decision on mobile: {decision}"
    except Exception as e:
        logger.error(f"Failed to request mobile approval: {e}")
        return f"❌ Error waiting for mobile approval: {str(e)}"

@mcp.tool()
async def mobile_remote_turn(
    prompt_context: str = "Workspace is ready. What would you like me to do next?",
    timeout_seconds: int = 600
) -> str:
    """
    Pushes a status/prompt message to the user's mobile phone and awaits their next text instruction.
    Use this when the user says they are stepping away from their desk and want to drive
    the session turn-by-turn from mobile.
    """
    try:
        async with httpx.AsyncClient(timeout=float(timeout_seconds + 15)) as client:
            resp = await client.post(
                f"{BASE_URL}/api/remote_turn",
                json={"prompt_context": prompt_context, "timeout": timeout_seconds}
            )
            resp.raise_for_status()
            instruction = resp.json().get("instruction", "No instruction received")
            return f"User instruction via mobile: {instruction}"
    except Exception as e:
        logger.error(f"Failed to receive mobile instruction: {e}")
        return f"❌ Error waiting for mobile instruction: {str(e)}"

def main():
    mcp.run()

if __name__ == "__main__":
    main()
