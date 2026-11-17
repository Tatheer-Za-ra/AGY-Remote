import asyncio
import logging
import uuid
import subprocess
from typing import Dict, List, Optional, Set
from fastapi import WebSocket
from .config import config

logger = logging.getLogger("antigravity_companion.pwa_bridge")

class PWABridge:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self._pending_approvals: Dict[str, asyncio.Future] = {}
        self._pending_user_input: Optional[asyncio.Future] = None
        self._prompt_queue: asyncio.Queue = asyncio.Queue()
        self.public_url: str = ""

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"Mobile PWA client connected. Active connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        logger.info(f"Mobile PWA client disconnected. Active connections: {len(self.active_connections)}")

    async def broadcast(self, data: dict):
        dead_connections = set()
        for connection in list(self.active_connections):
            try:
                await connection.send_json(data)
            except Exception:
                dead_connections.add(connection)
        for dead in dead_connections:
            self.active_connections.discard(dead)

    async def handle_incoming(self, message: dict):
        """Handles messages sent from mobile phone via WebSocket."""
        msg_type = message.get("type")

        if msg_type == "approval_response":
            approval_id = message.get("id")
            decision = message.get("decision")
            future = self._pending_approvals.get(approval_id)
            if future and not future.done():
                future.set_result(decision)
                logger.info(f"Approval {approval_id} resolved with decision: '{decision}'")

        elif msg_type == "prompt":
            text = message.get("text", "").strip()
            if not text:
                return

            logger.info(f"Incoming mobile prompt: '{text}'")

            # If listener is actively waiting, fulfill it immediately
            if self._pending_user_input and not self._pending_user_input.done():
                self._pending_user_input.set_result(text)
                self._pending_user_input = None
                logger.info(f"Delivered prompt directly to waiting listener: '{text}'")
            else:
                # Otherwise, place it in the FIFO queue so it is NEVER lost
                await self._prompt_queue.put(text)
                logger.info(f"Queued prompt for next agent turn: '{text}' (Queue size: {self._prompt_queue.qsize()})")

    async def send_notification(self, title: str, message: str, code: Optional[str] = None):
        payload = {
            "type": "notification",
            "title": title,
            "message": message,
            "code": code
        }
        await self.broadcast(payload)

    async def ask_approval(self, question: str, options: Optional[List[str]] = None, timeout: int = 300) -> str:
        if not options:
            options = ["Approve", "Deny"]

        approval_id = str(uuid.uuid4())[:8]
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        self._pending_approvals[approval_id] = future

        payload = {
            "type": "approval",
            "id": approval_id,
            "question": question,
            "options": options
        }
        await self.broadcast(payload)

        try:
            result = await asyncio.wait_for(future, timeout=float(timeout))
            return result
        except asyncio.TimeoutError:
            return f"Timeout: No response from mobile after {timeout} seconds."
        finally:
            self._pending_approvals.pop(approval_id, None)

    async def wait_for_instruction(self, prompt_context: str, timeout: int = 600) -> str:
        # Check if there is already a queued prompt in memory
        if not self._prompt_queue.empty():
            queued_text = await self._prompt_queue.get()
            logger.info(f"Immediately fulfilling listener from queued prompt: '{queued_text}'")
            return queued_text

        loop = asyncio.get_running_loop()
        future = loop.create_future()
        self._pending_user_input = future

        if prompt_context:
            payload = {
                "type": "remote_prompt",
                "prompt_context": prompt_context
            }
            await self.broadcast(payload)

        try:
            result = await asyncio.wait_for(future, timeout=float(timeout))
            return result
        except asyncio.TimeoutError:
            return f"Timeout: No instruction received after {timeout} seconds."
        finally:
            self._pending_user_input = None

bridge = PWABridge()
