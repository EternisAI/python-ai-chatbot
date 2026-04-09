from typing import Optional, List
from slack_sdk.web.slack_response import SlackResponse
import logging

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

"""
Parses a conversation history, excluding messages from the bot,
and formats it as a string with user IDs and their messages.
Used in `app_mentioned_callback`, `dm_sent_callback`,
and `handle_summary_function_callback`."""

IMAGE_MIMETYPES = {"image/png", "image/jpeg", "image/gif", "image/webp"}


def parse_conversation(conversation: SlackResponse) -> Optional[List[dict]]:
    parsed = []
    try:
        for message in conversation:
            user = message["user"]
            text = message["text"]
            parsed.append({"user": user, "text": text})
        return parsed
    except Exception as e:
        logger.error(e)
        return None


def extract_image_files(conversation: SlackResponse) -> List[dict]:
    """Extract image file info (url + mimetype) from conversation messages."""
    images = []
    for message in conversation:
        files = message.get("files", [])
        for f in files:
            mimetype = f.get("mimetype", "")
            if mimetype in IMAGE_MIMETYPES and f.get("url_private"):
                images.append({"url": f["url_private"], "mimetype": mimetype})
    return images
