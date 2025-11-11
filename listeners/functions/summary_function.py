from ai.providers import get_provider_response
from logging import Logger
from slack_bolt import Complete, Fail, Ack
from slack_sdk import WebClient
from ..listener_utils.listener_constants import SUMMARIZE_CHANNEL_WORKFLOW
from ..listener_utils.parse_conversation import parse_conversation

"""
Handles the event to summarize a Slack channel's conversation history.
It retrieves the conversation history, parses it, generates a summary using an AI response,
and completes the workflow with the summary or fails if an error occurs.
"""


def handle_summary_function_callback(
    ack: Ack,
    inputs: dict,
    fail: Fail,
    logger: Logger,
    client: WebClient,
    complete: Complete,
):
    ack()
    
    user_context = inputs.get("user_context", {})
    channel_id = inputs.get("channel_id")
    user_id = user_context.get("id", "unknown")
    
    logger.info(f"[summary_function] Summary request from user {user_id} for channel {channel_id}")
    
    try:
        logger.info(f"[summary_function] Fetching channel history...")
        history = client.conversations_history(channel=channel_id, limit=10)["messages"]
        logger.info(f"[summary_function] Retrieved {len(history)} messages")
        
        logger.info(f"[summary_function] Parsing conversation...")
        conversation = parse_conversation(history)
        logger.info(f"[summary_function] Parsed {len(conversation)} conversation items")

        logger.info(f"[summary_function] Generating summary...")
        summary = get_provider_response(
            user_id, SUMMARIZE_CHANNEL_WORKFLOW, conversation
        )
        logger.info(f"[summary_function] Summary generated (length: {len(summary)})")
        logger.debug(f"[summary_function] Summary preview: {summary[:200]}...")

        logger.info(f"[summary_function] Completing workflow...")
        complete({"user_context": user_context, "response": summary})
        logger.info(f"[summary_function] Workflow completed successfully!")
    except Exception as e:
        logger.error(f"[summary_function] ERROR: {type(e).__name__}: {str(e)}", exc_info=True)
        fail(e)
