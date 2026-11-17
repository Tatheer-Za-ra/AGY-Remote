# Antigravity Mobile Companion 📱

A secure, production-grade Mobile Companion & Remote Control Progressive Web App (PWA) and Plugin for **Google Antigravity IDE**.

Control your active desktop Antigravity IDE workspace, monitor tasks, receive instant notifications, review execution requests, and prompt your desktop agent directly from your phone — with **ZERO required clicks on the desktop screen**.

---

## ✨ Features

- **Bidirectional Control**: Send prompts, follow-ups, and instructions from your smartphone directly into the desktop agent session via a persistent FIFO queue.
- **True Mobile-First Permission Model**:
  - **Companion Mode ON**: All companion communication commands are automatically granted in `config.json`. Unapproved commands pause desktop execution and broadcast an interactive card with 4 touch buttons directly to your mobile screen.
  - **Dynamic In-IDE Grant Sync**: When you tap an approval option on mobile, the grant is injected into the IDE's configuration on the fly, eliminating desktop popups completely. Single-use grants are automatically cleaned up after execution via `PostToolUse`.
  - **Companion Mode OFF**: Automatically cleans up all companion grants and reverts to standard desktop review (`ask`), ensuring full local security when you return to your desk.
- **Interactive 4-Option Mobile Approvals**:
  1. `Yes, allow this time` (Single-use execution)
  2. `Yes, and always allow in this conversation` (Session-scoped)
  3. `Yes, and always allow` (Permanent global allowlist)
  4. `No (deny execution)` (Immediate block & cancel)
- **Audio & Haptic Feedback**: Synthesized Web Audio alert chimes and `navigator.vibrate` haptic pulses alert you when your attention is required.
- **Standalone PWA**: Installable as a native full-screen app on iOS Safari and Android Chrome with zero third-party messaging apps required (no Telegram, no Discord, no VPN).
- **Persistent Remote Tunnels**: Built-in support for authenticated **Ngrok** persistent tunnels as well as Cloudflare and local LAN Wi-Fi access.

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -e .
```

### 2. Configure Environment
Copy `.env.example` to `.env` and configure your settings:
```bash
cp .env.example .env
```
*(Optionally provide your Ngrok authtoken in `.env` for persistent 4G/5G remote access).*

### 3. Start Companion Mode
```bash
python run_companion.py
```

### 4. Connect on Mobile
Open the displayed pairing URL on your smartphone browser (or scan the terminal QR code):
- **Remote 4G/5G**: `https://<your-subdomain>.ngrok-free.dev/?token=agy_remote_secure_key`
- **Local Wi-Fi**: `http://<your-lan-ip>:8765/?token=agy_remote_secure_key`

---

## 🛡️ Permission Architecture

```text
┌────────────────────────────────────────────────────────────────┐
│ 📱 Mobile Companion Mode Active                                │
│                                                                │
│ 1. Companion Infra & Diagnostics: Auto-allowed (0 mobile buzz) │
│ 2. Command Execution Requests: Routed to Mobile Screen         │
│    [ 1. Yes, allow this time                         ]         │
│    [ 2. Yes, and always allow in this conversation  ]         │
│    [ 3. Yes, and always allow                        ]         │
│    [ 4. No (deny execution)                          ]         │
│                                                                │
│ 3. Mobile decision synchronizes directly into config.json     │
│ 4. Desktop IDE runs command silently with 0 desktop dialogs    │
│ 5. When Companion Mode stops -> Cleanly reverts to desktop ask │
└────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ MCP Tools Exposed

- `mobile_notify(title, message, code)`: Pushes a notification card to the mobile screen.
- `mobile_ask(question, options, timeout_seconds)`: Displays interactive touch buttons on mobile and awaits the user's decision.
- `mobile_remote_turn(prompt_context, timeout_seconds)`: Pushes status and awaits the next text instruction from mobile.

---

## 📜 License

MIT License. Built for Google Antigravity IDE.
