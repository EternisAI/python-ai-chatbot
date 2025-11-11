from ai.providers import get_provider_response
from logging import Logger
from slack_sdk import WebClient
from slack_bolt import Say
from ..listener_utils.listener_constants import (
    DEFAULT_LOADING_TEXT,
    MENTION_WITHOUT_TEXT,
)
from ..listener_utils.parse_conversation import parse_conversation

"""
Handles the event when the app is mentioned in a Slack channel, retrieves the conversation context,
and generates an AI response if text is provided, otherwise sends a default response
"""


def app_mentioned_callback(client: WebClient, event: dict, logger: Logger, say: Say):
    channel_id = event.get("channel")
    thread_ts = event.get("thread_ts")
    user_id = event.get("user")
    text = event.get("text")
    
    logger.info(f"[app_mentioned] Bot mentioned by user {user_id} in channel {channel_id}")
    logger.info(f"[app_mentioned] Message text: {text}")
    logger.info(f"[app_mentioned] Thread TS: {thread_ts}")
    
    waiting_message = None
    try:
        if thread_ts:
            logger.info(f"[app_mentioned] Fetching thread conversation...")
            conversation = client.conversations_replies(
                channel=channel_id, ts=thread_ts, limit=10
            )["messages"]
        else:
            logger.info(f"[app_mentioned] Fetching channel history...")
            conversation = client.conversations_history(channel=channel_id, limit=10)[
                "messages"
            ]
            thread_ts = event["ts"]

        conversation_context = parse_conversation(conversation[:-1])
        logger.info(f"[app_mentioned] Parsed {len(conversation_context)} messages from context")

        if text:
            logger.info(f"[app_mentioned] Sending waiting message...")
            waiting_message = say(text=DEFAULT_LOADING_TEXT, thread_ts=thread_ts)
            logger.info(f"[app_mentioned] Waiting message sent with ts: {waiting_message.get('ts')}")
            
            logger.info(f"[app_mentioned] Calling get_provider_response...")
            response = get_provider_response(user_id, text, conversation_context)
            logger.info(f"[app_mentioned] Received response from provider (length: {len(response)})")
            logger.debug(f"[app_mentioned] Response content: {response[:200]}...")
            
            logger.info(f"[app_mentioned] Updating message with response...")
            client.chat_update(
                channel=channel_id, ts=waiting_message["ts"], text=response
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
        logger.error(f"[app_mentioned] ERROR: {type(e).__name__}: {str(e)}", exc_info=True)
        if waiting_message:
            try:
                client.chat_update(
                    channel=channel_id,
                    ts=waiting_message["ts"],
                    text=f"Received an error from Bolty:\n{type(e).__name__}: {e}",
                )
            except Exception as update_error:
                logger.error(f"[app_mentioned] Failed to update error message: {update_error}", exc_info=True)
