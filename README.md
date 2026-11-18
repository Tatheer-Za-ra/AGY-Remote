# Antigravity Mobile Companion 📱

[![Antigravity Plugin](https://img.shields.io/badge/Antigravity-Plugin%20v1.0.0-blue.svg)](https://github.com/Tatheer-Za-ra/AGY-Remote)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

A secure, production-grade Mobile Companion & Remote Control Progressive Web App (PWA) and Official Plugin for **Google Antigravity IDE**.

Control your active desktop Antigravity IDE workspace, monitor tasks, receive instant notifications, review execution requests, and prompt your desktop agent directly from your phone — with **ZERO required clicks on the desktop screen**.

---

## ✨ Key Features

- **Bidirectional Control with Desktop Parity**: Send prompts, queue instructions, and follow up directly from your smartphone with continuous processing status and separate stop controls.
- **Dynamic Two-State Permission Gate**:
  - **Companion Mode Active**: Internal companion commands are automatically granted in `config.json`. Ungranted commands and sensitive file accesses pause desktop execution and broadcast an interactive card with 4 touch options directly to your mobile screen.
  - **Zero Desktop Popups**: When you approve on mobile, the grant dynamically injects into the IDE's configuration before execution. Single-use grants are automatically cleaned up immediately after tool execution via `PostToolUse`.
  - **Standby Mode**: Seamless low-power dormancy. Desktop permissions revert to standard workstation review while the tunnel stays alive.
- **Interactive 4-Option Mobile Approvals**:
  1. `Yes, allow this time` (Single-use execution)
  2. `Yes, and always allow in this conversation` (Session-scoped)
  3. `Yes, and always allow` (Permanent allowlist)
  4. `No (tell the agent what to do instead)` (Immediate block with custom guidance)
- **One-Tap Mobile Wakeup**: When in Standby, wake up Companion Mode at any time with a single tap on `[ ⚡ Turn On Companion Mode ]`, or simply type and send a prompt to wake it automatically!
- **Strict Floating Queue**: Prompts sent while the desktop agent is busy remain in a floating card above the input bar and are promoted sequentially only after the active turn response is delivered.
- **Persistent Remote Tunnels**: Built-in support for authenticated **Ngrok** persistent tunnels as well as Cloudflare and local LAN Wi-Fi access.
- **Audio & Haptic Feedback**: Synthesized Web Audio alert chimes and `navigator.vibrate` haptic pulses alert you when your attention is required.
- **Standalone PWA**: Installable as a native full-screen app on iOS Safari and Android Chrome with zero third-party messaging apps required (no Telegram, no Discord, no VPN).

---

## 📦 Plugin Architecture

```text
mobile-companion/
├── plugin.json              # Official Antigravity Extension Manifest (v1.0.0)
├── mcp_config.json          # Bundled MCP server configuration
├── hooks.json               # Bundled PreToolUse & PostToolUse lifecycle hooks
├── assets/logo.svg          # High-contrast official vector logo
├── rules/
│   └── AGENTS.md            # Zero-popup permission and queue separation rules
├── skills/
│   └── mobile-companion/
│       └── SKILL.md         # Operational documentation and tool definitions
├── scripts/
│   ├── remote_permission_gate.py   # PreToolUse gate & mobile router
│   ├── remote_post_tool.py         # PostToolUse cleanup & step emitter
│   ├── run_gate.bat                # Portable Windows runner
│   └── run_post_tool.bat           # Portable Windows cleanup runner
└── src/antigravity_companion/
    ├── web/index.html              # Desktop-parity responsive PWA
    ├── pwa_bridge.py               # WebSocket & FIFO queue orchestrator
    ├── permissions.py              # Dynamic config.json grant manager
    ├── tunnel.py                   # Ngrok & Cloudflare tunnel manager
    └── web_server.py               # FastAPI PWA & API endpoints
```

---

## 🚀 Installation & Quick Start

### Option A: Install from Antigravity Extensions Catalog
In Antigravity IDE, open the Customizations / Extensions view or chat:
```text
Install Antigravity Mobile Companion
```

### Option B: Local / Development Setup
1. **Clone the repository:**
   ```bash
   git clone https://github.com/Tatheer-Za-ra/AGY-Remote.git
   cd AGY-Remote
   ```

2. **Install dependencies:**
   ```bash
   pip install -e .
   ```

3. **Configure Environment:**
   Copy `.env.example` to `.env` and set your optional Ngrok authtoken and secure token:
   ```bash
   cp .env.example .env
   ```

4. **Start Companion Mode:**
   ```bash
   python run_companion.py
   ```

5. **Connect on Mobile:**
   Open the displayed pairing URL on your smartphone browser (or add to home screen as PWA):
   - **Remote 4G/5G**: `https://<your-subdomain>.ngrok-free.dev/?token=agy_remote_secure_key`
   - **Local Wi-Fi**: `http://<your-lan-ip>:8765/?token=agy_remote_secure_key`

---

## 🛡️ Permission Architecture Flow

```text
┌────────────────────────────────────────────────────────────────┐
│ 📱 Mobile Companion Mode Active                                │
│                                                                │
│ 1. Companion Infra & Diagnostics: Auto-allowed (0 mobile buzz) │
│ 2. Command Execution Requests: Routed to Mobile Screen         │
│    [ 1. Yes, allow this time                         ]         │
│    [ 2. Yes, and always allow in this conversation  ]         │
│    [ 3. Yes, and always allow                        ]         │
│    [ 4. No (tell the agent what to do instead)       ]         │
│                                                                │
│ 3. Mobile decision injects dynamically into config.json        │
│ 4. Desktop IDE executes command with 0 desktop dialog popups   │
│ 5. PostToolUse hook instantly cleans up single-use grants      │
│ 6. When Companion stops / Standby -> Reverts to desktop ask    │
└────────────────────────────────────────────────────────────────┘
```

---

## 📄 License

MIT © [Zara](https://github.com/Tatheer-Za-ra)
