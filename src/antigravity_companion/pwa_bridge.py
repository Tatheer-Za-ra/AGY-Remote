import asyncio
import logging
import uuid
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
        self._queued_prompts: List[dict] = []
        self._recent_steps: List[dict] = []
        self._active_step: Optional[dict] = None
        self._agent_state: str = "idle" # idle | thinking | working
        self.public_url: str = ""

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"Mobile PWA client connected. Active connections: {len(self.active_connections)}")
        
        # Send current state dump immediately so mobile client syncs state
        try:
            await websocket.send_json({
                "type": "init_state",
                "agent_state": self._agent_state,
                "active_step": self._active_step,
                "recent_steps": self._recent_steps[-10:],
                "queue": self._queued_prompts
            })
        except Exception:
            pass

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

    async def broadcast_agent_state(self, state: str, detail: str = ""):
        self._agent_state = state
        if state == "idle":
            self._active_step = None
        await self.broadcast({
            "type": "agent_state",
            "state": state,
            "detail": detail
        })

    async def broadcast_step(self, step_type: str, label: str, detail: str = "", is_code: bool = False):
        step_obj = {
            "id": str(uuid.uuid4())[:8],
            "step_type": step_type, # e.g. "tool_start", "tool_done", "analyzing", "running"
            "label": label,
            "detail": detail,
            "is_code": is_code
        }
        if step_type == "tool_start":
            self._active_step = step_obj
            self._agent_state = "working"
        elif step_type == "tool_done":
            self._recent_steps.append(step_obj)
            if len(self._recent_steps) > 30:
                self._recent_steps.pop(0)
            self._active_step = None

        await self.broadcast({
            "type": "progress_step",
            "step": step_obj
        })

    async def _broadcast_queue_update(self):
        await self.broadcast({
            "type": "queue_update",
            "queue": self._queued_prompts
        })

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

            prompt_id = message.get("id") or str(uuid.uuid4())[:8]
            logger.info(f"Incoming mobile prompt [{prompt_id}]: '{text}'")

            # If listener is actively waiting, fulfill it immediately
            if self._pending_user_input and not self._pending_user_input.done():
                self._agent_state = "working"
                self._pending_user_input.set_result(text)
                self._pending_user_input = None
                logger.info(f"Delivered prompt directly to waiting listener: '{text}'")
                await self.broadcast({
                    "type": "prompt_status",
                    "id": prompt_id,
                    "status": "processing",
                    "text": text
                })
            else:
                # Place in FIFO queue
                prompt_entry = {"id": prompt_id, "text": text}
                self._queued_prompts.append(prompt_entry)
                await self._prompt_queue.put(prompt_entry)
                logger.info(f"Queued prompt for next agent turn: '{text}' (Queue size: {self._prompt_queue.qsize()})")
                await self.broadcast({
                    "type": "prompt_queued",
                    "id": prompt_id,
                    "text": text,
                    "queue_position": len(self._queued_prompts)
                })
                await self.broadcast({
                    "type": "prompt_status",
                    "id": prompt_id,
                    "status": "queued",
                    "text": text,
                    "queue_position": len(self._queued_prompts)
                })
                await self._broadcast_queue_update()

    async def send_notification(self, title: str, message: str, code: Optional[str] = None):
        payload = {
            "type": "notification",
            "title": title,
            "message": message,
            "code": code
        }
        await self.broadcast(payload)

    async def ask_approval(self, question: str, options: Optional[List[str]] = None, timeout: int = 300, title: Optional[str] = None, target: Optional[str] = None) -> str:
        if not options:
            options = ["Approve", "Deny"]

        approval_id = str(uuid.uuid4())[:8]
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        self._pending_approvals[approval_id] = future

        payload = {
            "type": "approval",
            "id": approval_id,
            "title": title or "Permission Required",
            "target": target or question,
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
            item = await self._prompt_queue.get()
            queued_id = item.get("id") if isinstance(item, dict) else ""
            queued_text = item.get("text") if isinstance(item, dict) else str(item)
            
            # Remove from tracking list
            self._queued_prompts = [p for p in self._queued_prompts if p.get("id") != queued_id]
            await self._broadcast_queue_update()
            
            self._agent_state = "working"
            await self.broadcast({
                "type": "prompt_promoted",
                "id": queued_id,
                "status": "processing",
                "text": queued_text
            })
            await self.broadcast({
                "type": "prompt_status",
                "id": queued_id,
                "status": "processing",
                "text": queued_text
            })
            logger.info(f"Fulfilling listener from queued prompt: '{queued_text}'")
            return queued_text

        loop = asyncio.get_running_loop()
        future = loop.create_future()
        self._pending_user_input = future
        self._agent_state = "idle"

        if prompt_context:
            payload = {
                "type": "remote_prompt",
                "prompt_context": prompt_context
            }
            await self.broadcast(payload)

        await self.broadcast_agent_state("idle", "Waiting for user input...")

        try:
            result = await asyncio.wait_for(future, timeout=float(timeout))
            return result
        except asyncio.TimeoutError:
            return f"Timeout: No instruction received after {timeout} seconds."
        finally:
            self._pending_user_input = None

bridge = PWABridge()
