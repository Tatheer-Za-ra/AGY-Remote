import logging
from typing import Optional
from .config import config

logger = logging.getLogger("antigravity_companion.security")

def is_authorized(user_id: Optional[int]) -> bool:
    """Validates if the incoming Telegram user ID matches the authorized owner."""
    if not config.allowed_user_id or user_id is None:
        logger.warning("Authorization failed: No allowed_user_id configured.")
        return False
        
    authorized = (user_id == config.allowed_user_id)
    if not authorized:
        logger.warning(
            f"Unauthorized access attempt detected from Telegram User ID: {user_id}. Blocked."
        )
    return authorized

