from slack_bolt import Ack, Say, BoltContext
from logging import Logger
from ai.providers import get_provider_response
from slack_sdk import WebClient

"""
Callback for handling the 'ask-bolty' command. It acknowledges the command, retrieves the user's ID and prompt,
checks if the prompt is empty, and responds with either an error message or the provider's response.
"""


def ask_callback(
    client: WebClient, ack: Ack, command, say: Say, logger: Logger, context: BoltContext
):
    try:
        ack()
        user_id = context["user_id"]
        channel_id = context["channel_id"]
        prompt = command["text"]

        logger.info(f"[ask_command] Command received from user {user_id} in channel {channel_id}")
        logger.info(f"[ask_command] Prompt: {prompt}")

        if prompt == "":
            logger.warning(f"[ask_command] Empty prompt received")
            client.chat_postEphemeral(
                channel=channel_id,
                user=user_id,
                text="Looks like you didn't provide a prompt. Try again.",
            )
        else:
            logger.info(f"[ask_command] Calling get_provider_response...")
            response = get_provider_response(user_id, prompt)
            logger.info(f"[ask_command] Received response from provider (length: {len(response)})")
            logger.debug(f"[ask_command] Response content: {response[:200]}...")
            
            logger.info(f"[ask_command] Posting ephemeral message...")
            client.chat_postEphemeral(
                channel=channel_id,
                user=user_id,
                blocks=[
                    {
                        "type": "rich_text",
                        "elements": [
                            {
                                "type": "rich_text_quote",
                                "elements": [{"type": "text", "text": prompt}],
                            },
                            {
                                "type": "rich_text_section",
                                "elements": [
                                    {
                                        "type": "text",
                                        "text": response,
                                    }
                                ],
                            },
                        ],
                    }
                ],
            )
            logger.info(f"[ask_command] Message successfully posted!")
    except Exception as e:
        logger.error(f"[ask_command] ERROR: {type(e).__name__}: {str(e)}", exc_info=True)
        client.chat_postEphemeral(
            channel=channel_id, user=user_id, text=f"Received an error from Bolty:\n{type(e).__name__}: {e}"
        )
