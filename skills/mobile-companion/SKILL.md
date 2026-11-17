---
name: mobile-companion
description: Remote companion and notification controls for Google Antigravity IDE on mobile devices. Use when the user wants to monitor tasks remotely, send push notifications, request touch-button approvals on their phone, or receive turn-by-turn prompts while away from their desk.
---

# Antigravity Mobile Companion Skill

This skill allows the agent to communicate bidirectionally with the user's mobile device via a standalone Progressive Web App (PWA).

## 🛡️ Dynamic Two-State Permission Model

To provide a seamless remote experience without compromising desktop security, the Mobile Companion implements a dynamic two-state permission architecture:

### 1. When Companion Mode is ON (Remote Session Active):
- **Automated Communication**: All push notifications, status cards, audio chimes, and background listener processes are **automatically allowed** with zero desktop prompts.
- **Mobile Touch Redirection**: Any processing commands or file operations requiring user confirmation are **redirected directly to the user's phone screen** with the identical 4 desktop options:
  1. `Yes, allow this time`
  2. `Yes, and always allow in this conversation`
  3. `Yes, and always allow`
  4. `No (deny execution)`
- **Remote Decision Routing**: Tapping any option on the phone immediately transmits the decision to the desktop execution engine.

### 2. When Companion Mode is OFF (Desktop Session Active):
- The lifecycle hook automatically detects that the companion daemon is inactive and **instantly reverts to standard desktop permission review (`ask`)**.
- No permissions remain bypassed when the user is back at their workstation.

---

## Available Tools

1. `mobile_notify(title: str, message: str, code: Optional[str])`:
   - Sends an instant push notification card to the user's mobile phone screen.
   - Triggers a synthesized Web Audio chime and `navigator.vibrate` haptic feedback.
   - Use this to report task completion, test results, build errors, or summary updates.

2. `mobile_ask(question: str, options: List[str] = ["Approve", "Deny"], timeout_seconds: int = 300)`:
   - Displays interactive touch buttons directly on the user's mobile screen.
   - Blocks execution until the user taps an option on their phone or timeout expires.
   - Use this before running destructive actions, merging PRs, deploying, or deleting files.

3. `mobile_remote_turn(prompt_context: str, timeout_seconds: int = 600)`:
   - Pushes an update to the user's phone and awaits their next text prompt.
   - Allows turn-by-turn interactive steering of the desktop session while away from desk.

4. `mobile_get_connection_url()`:
   - Retrieves the active local Wi-Fi pairing URL and Cloudflare Tunnel 4G/5G remote URL.
