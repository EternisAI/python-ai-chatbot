import logging
from typing import List, Optional

from ..ai_constants import DEFAULT_SYSTEM_CONTENT
from .anthropic import AnthropicAPI
from .openai import OpenAI_API
from .vertexai import VertexAPI

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

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


def get_provider_response(
    user_id: str,
    prompt: str,
    context: Optional[List] = [],
    system_content=DEFAULT_SYSTEM_CONTENT,
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

        # Use GPT-5 for all users
        provider_name = "openai"
        model_name = "gpt-5-chat-latest"
        logger.info(
            f"[get_provider_response] Using model: {model_name} from provider: {provider_name} for user: {user_id}"
        )

        logger.info(f"[get_provider_response] Initializing provider: {provider_name}")
        provider = _get_provider(provider_name)

        logger.info(f"[get_provider_response] Setting model: {model_name}")
        provider.set_model(model_name)

        logger.info(f"[get_provider_response] Calling provider.generate_response()...")
        response = provider.generate_response(full_prompt, system_content)

        logger.info(
            f"[get_provider_response] Response received! Length: {len(response)}"
        )
        logger.debug(f"[get_provider_response] Response preview: {response[:200]}...")

        return response
    except Exception as e:
        logger.error(
            f"[get_provider_response] ERROR: {type(e).__name__}: {str(e)}",
            exc_info=True,
        )
        raise e
