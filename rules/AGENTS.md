# Rules for Mobile Companion Integration

When working with a user who is using the Antigravity Mobile Companion:

1. **Remote-First & Desktop Parity UX**: 
   - When Companion Mode is active, all major status updates, task completions, and interactive decision prompts must route directly to the mobile PWA.
   - Maintain strict desktop parity: the mobile UI features an auto-expanding multiline input, Enter key for newlines, separate Send/Queue button, and dedicated Stop control.

2. **Sequential Turn Ordering**:
   - Always deliver the agent response (`mobile_notify` + visible output) to the user *before* promoting the next queued prompt into the active chat feed.
   - Never pop a queued prompt ahead of completing the response to the current turn.

3. **Strict Floating Queue Separation**:
   - Queued prompts submitted while a task is processing must remain strictly in the floating queued card above the input bar.
   - Never allow a queued prompt to appear in the active chat feed until its execution actually begins.

4. **Dynamic Two-State Permission Gate**:
   - When Companion Mode is ON, all ungranted terminal commands and sensitive file accesses automatically route to mobile touch buttons with the 4 desktop options:
     1. `Yes, allow this time`
     2. `Yes, and always allow in this conversation`
     3. `Yes, and always allow`
     4. `No (tell the agent what to do instead)`
   - Dynamically inject approved grants into `config.json` before tool execution to guarantee **zero desktop modal popups**.
   - Clean up single-use grants immediately after tool execution via `PostToolUse`.
   - When Companion Mode is turned OFF, automatically revert all companion grants to restore standard workstation review.

5. **Performance & Low-Latency Pipeline**:
   - Use the fast-path local marker check (`.companion_active`) to test Companion Mode status in 0.01ms rather than issuing HTTP requests on every tool execution.
   - Keep the mobile prompt listener active in the background without redundant polling loops.
