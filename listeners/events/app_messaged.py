from logging import Logger

from slack_bolt import Say
from slack_sdk import WebClient

from ai.ai_constants import DM_SYSTEM_CONTENT
from ai.providers import get_provider_response

from ..listener_utils.listener_constants import DEFAULT_LOADING_TEXT
from ..listener_utils.message_utils import send_long_message
from ..listener_utils.parse_conversation import parse_conversation, extract_image_files

"""
Handles the event when a direct message is sent to the bot, retrieves the conversation context,
and generates an AI response.
"""


def app_messaged_callback(client: WebClient, event: dict, logger: Logger, say: Say):
    channel_id = event.get("channel")
    thread_ts = event.get("thread_ts")
    user_id = event.get("user")
    text = event.get("text")

    logger.info(
        f"[app_messaged] Received message from user {user_id} in channel {channel_id}"
    )
    logger.info(f"[app_messaged] Message text: {text}")
    logger.info(f"[app_messaged] Thread TS: {thread_ts}")
    logger.info(f"[app_messaged] Channel type: {event.get('channel_type')}")

    waiting_message = None
    try:
        if event.get("channel_type") == "im":
            conversation_context = ""

            if thread_ts:  # Retrieves context to continue the conversation in a thread.
                logger.info(f"[app_messaged] Fetching thread context for {thread_ts}")
                conversation = client.conversations_replies(
                    channel=channel_id, limit=200, ts=thread_ts
                )["messages"]
                conversation_context = parse_conversation(conversation[:-1])
                logger.info(
                    f"[app_messaged] Parsed {len(conversation_context)} messages from thread"
                )

            logger.info(f"[app_messaged] Sending waiting message...")
            waiting_message = say(text=DEFAULT_LOADING_TEXT, thread_ts=thread_ts)
            logger.info(
                f"[app_messaged] Waiting message sent with ts: {waiting_message.get('ts')}"
            )

            # Check if user wants images included
            include_images = "include images" in text.lower()
            image_files = []
            if include_images:
                if thread_ts:
                    for i, msg in enumerate(conversation):
                        files = msg.get("files")
                        if files:
                            logger.info(f"[app_messaged] Message {i} has {len(files)} files: {[{k: f.get(k) for k in ('id', 'name', 'mimetype', 'url_private', 'url_private_download', 'file_access')} for f in files]}")
                    image_files = extract_image_files(conversation)

                # Also include images from the current message itself
                event_files = event.get("files")
                logger.info(f"[app_messaged] Current event files: {event_files}")
                image_files.extend(extract_image_files([event]))
                logger.info(f"[app_messaged] Total extracted image files: {len(image_files)}: {image_files}")

            logger.info(f"[app_messaged] Calling get_provider_response...")
            response = get_provider_response(
                user_id, text, conversation_context, DM_SYSTEM_CONTENT,
                image_files=image_files if include_images else None,
                bot_token=client.token if include_images else None,
            )
            logger.info(
                f"[app_messaged] Received response from provider (length: {len(response)})"
            )
            logger.debug(f"[app_messaged] Response content: {response[:200]}...")

            logger.info(f"[app_messaged] Updating message with response...")
            send_long_message(
                client,
                channel_id,
                thread_ts or waiting_message["ts"],
                waiting_message["ts"],
                response,
            )
            logger.info(f"[app_messaged] Message successfully updated!")
    except Exception as e:
        logger.error(
            f"[app_messaged] ERROR: {type(e).__name__}: {str(e)}", exc_info=True
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
                    f"[app_messaged] Failed to update error message: {update_error}",
                    exc_info=True,
                )
