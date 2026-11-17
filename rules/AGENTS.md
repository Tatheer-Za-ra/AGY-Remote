# Rules for Mobile Companion Integration

When working with a user who is using the Antigravity Mobile Companion:

1. **Remote-First UX**: When the user indicates they are away from their desk or interacting from mobile, push all major status updates, task completions, and interactive decision prompts directly to the mobile PWA via `mobile_notify` or `mobile_ask`.
2. **Concise Formatting**: Format mobile cards cleanly. Avoid multi-screen wall of text in the mobile notification payloads; summarize high-level outcomes clearly.
3. **Continuous Responsiveness**: Keep the mobile listener active so any prompt sent by the user from their phone immediately wakes the desktop agent.
4. **Autonomous Mode**: For unattended remote usage, advise the user to set their IDE Tool Execution Policy to `always-proceed` so shell operations do not block on desktop permission popups.

