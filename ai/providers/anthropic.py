from .base_provider import BaseAPIProvider
import anthropic
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class AnthropicAPI(BaseAPIProvider):
    MODELS = {
        "claude-3-5-sonnet-20240620": {
            "name": "Claude 3.5 Sonnet",
            "provider": "Anthropic",
            "max_tokens": 4096,  # or 8192 with the header anthropic-beta: max-tokens-3-5-sonnet-2024-07-15
        },
        "claude-3-sonnet-20240229": {
            "name": "Claude 3 Sonnet",
            "provider": "Anthropic",
            "max_tokens": 4096,
        },
        "claude-3-haiku-20240307": {
            "name": "Claude 3 Haiku",
            "provider": "Anthropic",
            "max_tokens": 4096,
        },
        "claude-3-opus-20240229": {
            "name": "Claude 3 Opus",
            "provider": "Anthropic",
            "max_tokens": 4096,
        },
    }

    def __init__(self):
        self.api_key = os.environ.get("ANTHROPIC_API_KEY")

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
        logger.info(f"[Anthropic] Generating response with model: {self.current_model}")
        logger.info(f"[Anthropic] API key present: {bool(self.api_key)}")
        logger.info(f"[Anthropic] Prompt length: {len(prompt)}")
        logger.info(f"[Anthropic] System content length: {len(system_content)}")
        
        try:
            logger.info(f"[Anthropic] Initializing Anthropic client...")
            self.client = anthropic.Anthropic(api_key=self.api_key)
            
            logger.info(f"[Anthropic] Making API request to {self.current_model}...")
            logger.debug(f"[Anthropic] System content: {system_content[:200]}...")
            logger.debug(f"[Anthropic] Prompt: {prompt[:200]}...")
            
            response = self.client.messages.create(
                model=self.current_model,
                system=system_content,
                messages=[
                    {"role": "user", "content": [{"type": "text", "text": prompt}]}
                ],
                max_tokens=self.MODELS[self.current_model]["max_tokens"],
            )
            
            logger.info(f"[Anthropic] API request successful!")
            logger.info(f"[Anthropic] Response type: {type(response)}")
            logger.debug(f"[Anthropic] Response object: {response}")
            
            result = response.content[0].text
            logger.info(f"[Anthropic] Output text length: {len(result)}")
            logger.debug(f"[Anthropic] Output text preview: {result[:200]}...")
            
            return result
        except anthropic.APIConnectionError as e:
            logger.error(f"[Anthropic] Server could not be reached: {e.__cause__}", exc_info=True)
            raise e
        except anthropic.RateLimitError as e:
            logger.error(f"[Anthropic] A 429 status code was received. {e}", exc_info=True)
            raise e
        except anthropic.AuthenticationError as e:
            logger.error(f"[Anthropic] There's an issue with your API key. {e}", exc_info=True)
            raise e
        except anthropic.APIStatusError as e:
            logger.error(
                f"[Anthropic] Another non-200-range status code was received: {e.status_code}", exc_info=True
            )
            raise e
        except Exception as e:
            logger.error(f"[Anthropic] Unexpected error: {type(e).__name__}: {str(e)}", exc_info=True)
            raise e
