import os
import json
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from .config import config
from .pwa_bridge import bridge

app = FastAPI(title="Antigravity Mobile Companion")

WEB_DIR = Path(__file__).parent / "web"

@app.get("/", response_class=HTMLResponse)
async def serve_index(token: str = Query(None)):
    index_file = WEB_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=404, detail="Web assets missing")
    with open(index_file, "r", encoding="utf-8") as f:
        content = f.read()
    return HTMLResponse(content)

@app.get("/manifest.json")
async def serve_manifest():
    manifest_file = WEB_DIR / "manifest.json"
    if not manifest_file.exists():
        raise HTTPException(status_code=404, detail="Manifest missing")
    with open(manifest_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    return JSONResponse(data)

@app.post("/api/notify")
async def api_notify(payload: dict):
    title = payload.get("title", "Desktop Alert")
    message = payload.get("message", "")
    code = payload.get("code")
    await bridge.send_notification(title, message, code)
    return {"status": "delivered"}

@app.post("/api/ask")
async def api_ask(payload: dict):
    question = payload.get("question", "Approval requested")
    options = payload.get("options", ["Approve", "Deny"])
    timeout = payload.get("timeout", 300)
    decision = await bridge.ask_approval(question, options, timeout=timeout)
    return {"decision": decision}

@app.post("/api/remote_turn")
async def api_remote_turn(payload: dict):
    prompt_context = payload.get("prompt_context", "Waiting for instruction...")
    timeout = payload.get("timeout", 600)
    instruction = await bridge.wait_for_instruction(prompt_context, timeout=timeout)
    return {"instruction": instruction}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(None)):
    # Validate token for security
    if token != config.secret_token:
        await websocket.close(code=1008) # Policy Violation
        return

    await bridge.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            await bridge.handle_incoming(data)
    except WebSocketDisconnect:
        bridge.disconnect(websocket)
    except Exception:
        bridge.disconnect(websocket)

