from logging import Logger

from slack_bolt import Say
from slack_sdk import WebClient

from ai.providers import get_provider_response

from ..listener_utils.listener_constants import (
    DEFAULT_LOADING_TEXT,
    MENTION_WITHOUT_TEXT,
)
from ..listener_utils.message_utils import send_long_message
from ..listener_utils.parse_conversation import parse_conversation, extract_image_files

"""
Handles the event when the app is mentioned in a Slack channel, retrieves the conversation context,
and generates an AI response if text is provided, otherwise sends a default response
"""


def app_mentioned_callback(client: WebClient, event: dict, logger: Logger, say: Say):
    channel_id = event.get("channel")
    thread_ts = event.get("thread_ts")
    user_id = event.get("user")
    text = event.get("text")

    logger.info(
        f"[app_mentioned] Bot mentioned by user {user_id} in channel {channel_id}"
    )
    logger.info(f"[app_mentioned] Message text: {text}")
    logger.info(f"[app_mentioned] Thread TS: {thread_ts}")

    waiting_message = None
    try:
        if thread_ts:
            logger.info(f"[app_mentioned] Fetching thread conversation...")
            conversation = client.conversations_replies(
                channel=channel_id, ts=thread_ts, limit=200
            )["messages"]
        else:
            logger.info(f"[app_mentioned] Fetching channel history...")
            conversation = client.conversations_history(channel=channel_id, limit=200)[
                "messages"
            ]
            thread_ts = event["ts"]

        conversation_context = parse_conversation(conversation[:-1])
        logger.info(
            f"[app_mentioned] Parsed {len(conversation_context)} messages from context"
        )

        if text:
            logger.info(f"[app_mentioned] Sending waiting message...")
            waiting_message = say(text=DEFAULT_LOADING_TEXT, thread_ts=thread_ts)
            logger.info(
                f"[app_mentioned] Waiting message sent with ts: {waiting_message.get('ts')}"
            )

            # Check if user wants images included
            include_images = "include images" in text.lower()
            image_files = []
            if include_images:
                # Debug: log raw files from each message
                for i, msg in enumerate(conversation):
                    files = msg.get("files")
                    if files:
                        logger.info(f"[app_mentioned] Message {i} has {len(files)} files: {[{k: f.get(k) for k in ('id', 'name', 'mimetype', 'url_private', 'url_private_download', 'file_access')} for f in files]}")
                    else:
                        logger.info(f"[app_mentioned] Message {i} has no files. Keys: {list(msg.keys())}")

                image_files = extract_image_files(conversation)
                logger.info(f"[app_mentioned] Extracted {len(image_files)} image files: {image_files}")

            logger.info(f"[app_mentioned] Calling get_provider_response...")
            response = get_provider_response(
                user_id, text, conversation_context,
                image_files=image_files if include_images else None,
                bot_token=client.token if include_images else None,
            )
            logger.info(
                f"[app_mentioned] Received response from provider (length: {len(response)})"
            )
            logger.debug(f"[app_mentioned] Response content: {response[:200]}...")

            logger.info(f"[app_mentioned] Updating message with response...")
            send_long_message(
                client, channel_id, thread_ts, waiting_message["ts"], response
            )
            logger.info(f"[app_mentioned] Message successfully updated!")
        else:
            logger.warning(f"[app_mentioned] No text provided in mention")
            response = MENTION_WITHOUT_TEXT
            if waiting_message:
                client.chat_update(
                    channel=channel_id, ts=waiting_message["ts"], text=response
                )

    except Exception as e:
        logger.error(
            f"[app_mentioned] ERROR: {type(e).__name__}: {str(e)}", exc_info=True
        )
        if waiting_message:
            try:
                error_text = f"Received an error from Bolty:\n{type(e).__name__}: {str(e)[:500]}"
                client.chat_update(
                    channel=channel_id,
                    ts=waiting_message["ts"],
                    text=error_text,
                )
            except Exception as update_error:
                logger.error(
                    f"[app_mentioned] Failed to update error message: {update_error}",
                    exc_info=True,
                )
