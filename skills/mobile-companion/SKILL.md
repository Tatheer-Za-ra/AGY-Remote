---
name: mobile-companion
description: Remote companion and notification controls for Google Antigravity IDE on mobile devices. Use when the user wants to monitor tasks remotely, send push notifications, request touch-button approvals on their phone, or receive turn-by-turn prompts while away from their desk.
---

# Antigravity Mobile Companion Skill

This skill allows the agent to communicate bidirectionally with the user's mobile device via a standalone Progressive Web App (PWA).

## 🛡️ Dynamic Two-State Permission Model

To provide a seamless remote experience with desktop parity and zero desktop popups, the Mobile Companion implements a dynamic two-state permission architecture:

### 1. When Companion Mode is ON (Remote Session Active):
- **Automated Communication**: All internal companion infrastructure (`mobile_listener.py`, `gate.log`, `tasklist`, `netstat`, `git`) is automatically allowed without desktop popups or mobile spam.
- **Mobile Touch Redirection**: Any ungranted terminal commands or sensitive file accesses (`.env`, certificates) are redirected directly to the user's phone screen with the 4 standard desktop options:
  1. `Yes, allow this time`
  2. `Yes, and always allow in this conversation`
  3. `Yes, and always allow`
  4. `No (tell the agent what to do instead)`
- **Dynamic Grant Injection**: Approved decisions inject directly into `~/.gemini/config/config.json` before execution, ensuring **zero desktop popups** on the physical monitor.
- **Single-Use Auto-Cleanup**: The `PostToolUse` lifecycle hook immediately cleans single-use grants after tool execution.

### 2. When Companion Mode is OFF (Workstation Active):
- The lifecycle hook automatically detects that `.companion_active` is absent and instantly reverts to standard desktop permission review (`ask`).
- All companion grants are safely reverted in `config.json`.

---

## ⏳ Strict Floating Queue & Promotion Protocol

When processing tasks:
1. **Floated Condition**: Any prompt submitted while the desktop is busy docks exclusively in a floating queued card above the input box.
2. **Sequential Promotion**: When a task completes, its response card must be pushed to the user **first**.
3. **Upload to Feed**: Only after the response is delivered is the next queued prompt promoted from the floating box into the active chat feed.

---

## ⚡ Performance Optimization

- **Fast-Path Check**: Companion mode status is verified using a local `.companion_active` marker file (0.01ms check) rather than network roundtrips.
- **Single-Turn Execution**: Responses and background listener arming are handled in a single streamlined turn without redundant polling calls.

---

## Available Tools

1. `mobile_notify(title: str, message: str, code: Optional[str])`:
   - Sends an instant push notification card to the user's mobile phone screen.
   - Triggers a Web Audio chime and haptic feedback.
   - Use this to report task completion, test results, build errors, or summary updates.

2. `mobile_ask(question: str, options: List[str] = ["Approve", "Deny"], timeout_seconds: int = 300)`:
   - Displays interactive touch buttons directly on the user's mobile screen.
   - Blocks execution until the user taps an option on their phone or timeout expires.

3. `mobile_remote_turn(prompt_context: str, timeout_seconds: int = 600)`:
   - Pushes an update to the user's phone and awaits their next text prompt.
