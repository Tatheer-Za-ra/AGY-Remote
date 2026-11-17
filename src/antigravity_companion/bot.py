import asyncio
import logging
import uuid
from typing import Dict, List, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from .config import config
from .security import is_authorized
from .formatter import format_notification, chunk_text

logger = logging.getLogger("antigravity_companion.bot")

class CompanionBot:
    def __init__(self):
        self.app: Optional[Application] = None
        self._running = False
        self._pending_approvals: Dict[str, asyncio.Future] = {}
        self._pending_user_input: Optional[asyncio.Future] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    async def initialize(self):
        """Initializes and starts the Telegram bot long-polling engine."""
        if self._running:
            return

        config.validate()
        self._loop = asyncio.get_running_loop()
        self.app = ApplicationBuilder().token(config.bot_token).build()

        # Register handlers
        self.app.add_handler(CommandHandler("start", self._handle_start))
        self.app.add_handler(CommandHandler("status", self._handle_status))
        self.app.add_handler(CallbackQueryHandler(self._handle_callback))
        self.app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), self._handle_message))

        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling(drop_pending_updates=True)
        self._running = True
        logger.info("CompanionBot polling started successfully.")

    async def shutdown(self):
        """Gracefully shuts down the Telegram bot."""
        if self._running and self.app:
            await self.app.updater.stop()
            await self.app.stop()
            await self.app.shutdown()
            self._running = False
            logger.info("CompanionBot stopped.")

    async def _handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.effective_user or not is_authorized(update.effective_user.id):
            if update.message:
                await update.message.reply_text("⛔ Unauthorized. This bot is locked to its desktop owner.")
            return

        msg = (
            "🚀 <b>Antigravity Desktop Companion Connected!</b>\n\n"
            "Your mobile device is now linked to your desktop IDE.\n"
            "• You will receive notifications when tasks finish or need attention.\n"
            "• You will see interactive approval buttons for terminal/file operations.\n"
            "• Type any message here to send instructions to the desktop agent."
        )
        if update.message:
            await update.message.reply_text(msg, parse_mode=ParseMode.HTML)

    async def _handle_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.effective_user or not is_authorized(update.effective_user.id):
            return
        if update.message:
            await update.message.reply_text("🟢 <b>Desktop IDE Status:</b> Active and connected.", parse_mode=ParseMode.HTML)

    async def _handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        if not query or not query.from_user or not is_authorized(query.from_user.id):
            if query:
                await query.answer("Unauthorized", show_alert=True)
            return

        await query.answer()
        data = query.data or ""
        # Format: "approval_id:selected_option"
        if ":" in data:
            approval_id, selected_option = data.split(":", 1)
            future = self._pending_approvals.get(approval_id)
            if future and not future.done():
                future.set_result(selected_option)
                # Update the message text to show what was selected
                try:
                    await query.edit_message_reply_markup(reply_markup=None)
                    if query.message:
                        await query.message.reply_text(
                            f"✅ Decision recorded: <b>{selected_option}</b>",
                            parse_mode=ParseMode.HTML,
                        )
                except Exception as e:
                    logger.debug(f"Could not edit message markup: {e}")

    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.effective_user or not is_authorized(update.effective_user.id):
            return

        text = update.message.text if update.message else ""
        if not text:
            return

        # Check if an MCP tool is waiting for user input
        if self._pending_user_input and not self._pending_user_input.done():
            self._pending_user_input.set_result(text)
            self._pending_user_input = None
            if update.message:
                await update.message.reply_text("📥 <i>Instruction forwarded to Desktop IDE...</i>", parse_mode=ParseMode.HTML)
        else:
            if update.message:
                await update.message.reply_text(
                    "💡 Agent is currently idle or running a background task. Message received.",
                    parse_mode=ParseMode.HTML,
                )

    async def send_notification(self, title: str, message: str, code: Optional[str] = None) -> bool:
        """Sends a notification chunked for Telegram."""
        if not self._running or not self.app or not config.allowed_user_id:
            await self.initialize()

        chunks = format_notification(title, message, code)
        for chunk in chunks:
            await self.app.bot.send_message(
                chat_id=config.allowed_user_id,
                text=chunk,
                parse_mode=ParseMode.HTML,
            )
        return True

    async def ask_approval(
        self,
        question: str,
        options: Optional[List[str]] = None,
        timeout: int = 300,
    ) -> str:
        """Sends an interactive question with inline buttons and awaits the user's response."""
        if not self._running or not self.app or not config.allowed_user_id:
            await self.initialize()

        if not options:
            options = ["Approve", "Deny"]

        approval_id = str(uuid.uuid4())[:8]
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        self._pending_approvals[approval_id] = future

        keyboard = [
            [
                InlineKeyboardButton(
                    text=f"✅ {opt}" if "approve" in opt.lower() else (f"❌ {opt}" if "deny" in opt.lower() or "reject" in opt.lower() else opt),
                    callback_data=f"{approval_id}:{opt}",
                )
                for opt in options
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        msg_text = f"⚠️ <b>Approval Required:</b>\n\n{question}"
        await self.app.bot.send_message(
            chat_id=config.allowed_user_id,
            text=msg_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML,
        )

        try:
            result = await asyncio.wait_for(future, timeout=float(timeout))
            return result
        except asyncio.TimeoutError:
            return f"Timeout: No response from user after {timeout} seconds."
        finally:
            self._pending_approvals.pop(approval_id, None)

    async def wait_for_instruction(self, prompt_context: str, timeout: int = 600) -> str:
        """Prompts the user on mobile and blocks until they reply with text."""
        if not self._running or not self.app or not config.allowed_user_id:
            await self.initialize()

        loop = asyncio.get_running_loop()
        future = loop.create_future()
        self._pending_user_input = future

        msg_text = f"💬 <b>Desktop Agent Prompt:</b>\n\n{prompt_context}\n\n<i>Reply to this message with your next instruction.</i>"
        await self.app.bot.send_message(
            chat_id=config.allowed_user_id,
            text=msg_text,
            parse_mode=ParseMode.HTML,
        )

        try:
            result = await asyncio.wait_for(future, timeout=float(timeout))
            return result
        except asyncio.TimeoutError:
            return f"Timeout: No instruction received after {timeout} seconds."
        finally:
            self._pending_user_input = None

bot = CompanionBot()

