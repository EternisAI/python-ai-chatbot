import base64
import logging
import re
from datetime import datetime
from typing import List, Optional

import requests

from ..ai_constants import DEFAULT_SYSTEM_CONTENT
from .anthropic import AnthropicAPI
from .openai import OpenAI_API
from .vertexai import VertexAPI

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def convert_markdown_to_slack(text: str) -> str:
    """
    Convert standard markdown formatting to Slack mrkdwn format.
    - Links: [text](url) -> <url|text>
    - Bold: **text** -> *text*
    - Italic: *text* -> _text_ (tricky, need to handle carefully)
    """
    # Convert markdown links [text](url) to Slack format <url|text>
    text = re.sub(r"\[([^\]]+)\]\(([^\)]+)\)", r"<\2|\1>", text)

    # Convert **bold** to *bold* (Slack format)
    text = re.sub(r"\*\*([^\*]+)\*\*", r"*\1*", text)

    # Note: Converting single asterisk italics is complex because Slack uses underscores
    # and we need to avoid converting already-correct bold formatting
    # For now, we'll leave single asterisks as-is since they work for bold in Slack

    return text


"""
New AI providers must be added below.
`get_available_providers()`
This function retrieves available API models from different AI providers.
It combines the available models into a single dictionary.
`_get_provider()`
This function returns an instance of the appropriate API provider based on the given provider name.
`get_provider_response`()
This function retrieves the user's selected API provider and model,
sets the model, and generates a response.
Note that context is an optional parameter because some functionalities,
such as commands, do not allow access to conversation history if the bot
isn't in the channel where the command is run.
"""


def get_available_providers():
    return {
        **AnthropicAPI().get_models(),
        **OpenAI_API().get_models(),
        **VertexAPI().get_models(),
    }


def _get_provider(provider_name: str):
    if provider_name.lower() == "anthropic":
        return AnthropicAPI()
    elif provider_name.lower() == "openai":
        return OpenAI_API()
    elif provider_name.lower() == "vertexai":
        return VertexAPI()
    else:
        raise ValueError(f"Unknown provider: {provider_name}")


def download_slack_images(image_urls: List[str], bot_token: str) -> List[dict]:
    """Download images from Slack and return as base64 data URIs."""
    images = []
    headers = {"Authorization": f"Bearer {bot_token}"}
    for url in image_urls:
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            content_type = resp.headers.get("Content-Type", "image/png")
            b64 = base64.b64encode(resp.content).decode("utf-8")
            images.append({"url": f"data:{content_type};base64,{b64}"})
            logger.info(f"[download_slack_images] Downloaded image from {url[:80]}...")
        except Exception as e:
            logger.error(f"[download_slack_images] Failed to download {url}: {e}")
    return images


def get_provider_response(
    user_id: str,
    prompt: str,
    context: Optional[List] = [],
    system_content=DEFAULT_SYSTEM_CONTENT,
    image_urls: Optional[List[str]] = None,
    bot_token: Optional[str] = None,
):
    logger.info(f"[get_provider_response] Starting for user: {user_id}")
    logger.info(f"[get_provider_response] Prompt length: {len(prompt)}")
    logger.info(f"[get_provider_response] Context items: {len(context)}")
    logger.debug(f"[get_provider_response] Prompt: {prompt[:200]}...")

    try:
        formatted_context = "\n".join(
            [f"{msg['user']}: {msg['text']}" for msg in context]
        )
        full_prompt = f"Prompt: {prompt}\nContext: {formatted_context}"

        logger.info(f"[get_provider_response] Full prompt length: {len(full_prompt)}")
        logger.debug(
            f"[get_provider_response] Formatted context: {formatted_context[:200]}..."
        )

        # Download images from Slack and convert to base64
        images = []
        if image_urls and bot_token:
            logger.info(f"[get_provider_response] Downloading {len(image_urls)} images...")
            images = download_slack_images(image_urls, bot_token)
            logger.info(f"[get_provider_response] Successfully downloaded {len(images)} images")

        # Add current date to system prompt
        current_date = datetime.now().strftime("%A, %B %d, %Y")
        system_content_with_date = f"{system_content}\n\nCurrent date: {current_date}"
        logger.info(f"[get_provider_response] Current date: {current_date}")

        # Use GPT-5 for all users
        provider_name = "openai"
        model_name = "gpt-5.4"
        logger.info(
            f"[get_provider_response] Using model: {model_name} from provider: {provider_name} for user: {user_id}"
        )

        logger.info(f"[get_provider_response] Initializing provider: {provider_name}")
        provider = _get_provider(provider_name)

        logger.info(f"[get_provider_response] Setting model: {model_name}")
        provider.set_model(model_name)

        logger.info(f"[get_provider_response] Calling provider.generate_response()...")
        response = provider.generate_response(full_prompt, system_content_with_date, images=images)

        logger.info(
            f"[get_provider_response] Response received! Length: {len(response)}"
        )
        logger.debug(f"[get_provider_response] Response preview: {response[:200]}...")

        # Convert markdown formatting to Slack format
        response = convert_markdown_to_slack(response)
        logger.info(f"[get_provider_response] Converted to Slack formatting")

        return response
    except Exception as e:
        logger.error(
            f"[get_provider_response] ERROR: {type(e).__name__}: {str(e)}",
            exc_info=True,
        )
        raise e
