import os

from dotenv import load_dotenv

load_dotenv()


def _int(name: str, default: int = 0) -> int:
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


API_ID = _int("API_ID")
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
SESSION_STRING = os.getenv("SESSION_STRING", "")

OWNER_ID = _int("OWNER_ID")
LOG_CHAT_ID = _int("LOG_CHAT_ID")

# Optional: restrict the bot to a single group. 0 = allow every group.
ALLOWED_CHAT_ID = _int("ALLOWED_CHAT_ID")

COMMAND_PREFIXES = ["/", "!", "."]
