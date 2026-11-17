import asyncio
import time
import sys
from src.antigravity_companion.config import config
from src.antigravity_companion.pwa_bridge import bridge
from src.antigravity_companion.server import start_background_web_server

async def run_test():
    print("=" * 65)
    print("  🚀 Antigravity Mobile Companion PWA — Live Test")
    print("=" * 65)

    start_background_web_server()

    print("\n👉 [Step 1]: Open this link on your phone (Safari or Chrome):")
    print(f"\n   🔗 {bridge.public_url}\n")
    print("   (You can also test it in your PC browser right now!)")
    print("\n⏳ Waiting for phone to connect...")

    # Wait for at least one client to connect
    while len(bridge.active_connections) == 0:
        await asyncio.sleep(1)

    print("\n🎉 Mobile Phone Connected successfully!")
    print("\n[Step 2]: Sending test notification to phone...")
    await bridge.send_notification(
        title="Desktop Antigravity IDE Linked!",
        message="Your mobile phone is now communicating with your desktop IDE in real time.",
        code="def hello_mobile():\n    return 'Desktop hardware executing...'"
    )
    print("✅ Notification sent to phone!")

    print("\n[Step 3]: Sending interactive approval request to phone...")
    print("👉 Look at your phone screen and tap one of the buttons.")

    decision = await bridge.ask_approval(
        question="Do you approve this test run from your phone?",
        options=["Yes, looks great!", "Deny"],
        timeout=120
    )

    print(f"\n🎉 SUCCESS! Decision received from your phone: '{decision}'")
    print("\n=" * 65)
    print("  All systems verified! Ready to register in Antigravity IDE.")
    print("=" * 65)

if __name__ == "__main__":
    asyncio.run(run_test())
