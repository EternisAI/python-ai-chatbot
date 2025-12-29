import logging
import os

import openai

from .base_provider import BaseAPIProvider

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class OpenAI_API(BaseAPIProvider):
    MODELS = {
        "gpt-4.1": {"name": "GPT-4.1", "provider": "OpenAI", "max_tokens": 10000},
        "gpt-4.1-mini": {
            "name": "GPT-4.1 Mini",
            "provider": "OpenAI",
            "max_tokens": 10000,
        },
        "gpt-4.1-nano": {
            "name": "GPT-4.1 Nano",
            "provider": "OpenAI",
            "max_tokens": 10000,
        },
        "o4-mini": {"name": "o4-mini", "provider": "OpenAI", "max_tokens": 50000},
        "gpt-5.2-chat-latest": {
            "name": "gpt-5.2-chat-latest",
            "provider": "OpenAI",
            "max_tokens": 200000,
        },
    }

    def __init__(self):
        self.api_key = os.environ.get("OPENAI_API_KEY")

    def set_model(self, model_name: str):
        if model_name not in self.MODELS.keys():
            raise ValueError("Invalid model")
        self.current_model = model_name

    def get_models(self) -> dict:
        if self.api_key is not None:
            return self.MODELS
        else:
            return {}

    def generate_response(self, prompt: str, system_content: str) -> str:
        logger.info(f"[OpenAI] Generating response with model: {self.current_model}")
        logger.info(f"[OpenAI] API key present: {bool(self.api_key)}")
        logger.info(f"[OpenAI] Prompt length: {len(prompt)}")
        logger.info(f"[OpenAI] System content length: {len(system_content)}")

        try:
            logger.info(f"[OpenAI] Initializing OpenAI client...")
            self.client = openai.OpenAI(api_key=self.api_key)

            logger.info(
                f"[OpenAI] Making API request to {self.current_model} with web_search tool..."
            )
            logger.debug(f"[OpenAI] System content: {system_content[:200]}...")
            logger.debug(f"[OpenAI] Prompt: {prompt[:200]}...")

            response = self.client.responses.create(
                model=self.current_model,
                input=[
                    {"role": "developer", "content": system_content},
                    {"role": "user", "content": prompt},
                ],
                tools=[{"type": "web_search"}],
                max_output_tokens=self.MODELS[self.current_model]["max_tokens"],
            )

            logger.info(f"[OpenAI] API request successful!")
            logger.info(f"[OpenAI] Response type: {type(response)}")
            logger.debug(f"[OpenAI] Response object: {response}")

            result = response.output_text
            logger.info(f"[OpenAI] Output text length: {len(result)}")
            logger.debug(f"[OpenAI] Output text preview: {result[:200]}...")

            return result
        except openai.APIConnectionError as e:
            logger.error(
                f"[OpenAI] Server could not be reached: {e.__cause__}", exc_info=True
            )
            raise e
        except openai.RateLimitError as e:
            logger.error(f"[OpenAI] A 429 status code was received. {e}", exc_info=True)
            raise e
        except openai.AuthenticationError as e:
            logger.error(
                f"[OpenAI] There's an issue with your API key. {e}", exc_info=True
            )
            raise e
        except openai.APIStatusError as e:
            logger.error(
                f"[OpenAI] Another non-200-range status code was received: {e.status_code}",
                exc_info=True,
            )
            raise e
        except Exception as e:
            logger.error(
                f"[OpenAI] Unexpected error: {type(e).__name__}: {str(e)}",
                exc_info=True,
            )
            raise e
