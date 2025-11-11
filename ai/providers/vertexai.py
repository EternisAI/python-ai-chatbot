import logging
import os

import google.api_core.exceptions
import vertexai.generative_models

from .base_provider import BaseAPIProvider

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class VertexAPI(BaseAPIProvider):
    VERTEX_AI_PROVIDER = "VertexAI"
    MODELS = {
        "gemini-1.5-flash-001": {
            "name": "Gemini 1.5 Flash 001",
            "provider": VERTEX_AI_PROVIDER,
            "max_tokens": 8192,
            "system_instruction_supported": True,
        },
        "gemini-1.5-flash-002": {
            "name": "Gemini 1.5 Flash 002",
            "provider": VERTEX_AI_PROVIDER,
            "max_tokens": 8192,
            "system_instruction_supported": True,
        },
        "gemini-1.5-pro-002": {
            "name": "Gemini 1.5 Pro 002",
            "provider": VERTEX_AI_PROVIDER,
            "max_tokens": 8192,
            "system_instruction_supported": True,
        },
        "gemini-1.5-pro-001": {
            "name": "Gemini 1.5 Pro 001",
            "provider": VERTEX_AI_PROVIDER,
            "max_tokens": 8192,
            "system_instruction_supported": True,
        },
        "gemini-1.0-pro-002": {
            "name": "Gemini 1.0 Pro 002",
            "provider": VERTEX_AI_PROVIDER,
            "max_tokens": 8192,
            "system_instruction_supported": True,
        },
        "gemini-1.0-pro-001": {
            "name": "Gemini 1.0 Pro 001",
            "provider": VERTEX_AI_PROVIDER,
            "max_tokens": 8192,
            "system_instruction_supported": False,
        },
        "gemini-flash-experimental": {
            "name": "Gemini Flash Experimental",
            "provider": VERTEX_AI_PROVIDER,
            "max_tokens": 8192,
            "system_instruction_supported": True,
        },
        "gemini-pro-experimental": {
            "name": "Gemini Pro Experimental",
            "provider": VERTEX_AI_PROVIDER,
            "max_tokens": 8192,
            "system_instruction_supported": True,
        },
        "gemini-experimental": {
            "name": "Gemini Experimental",
            "provider": VERTEX_AI_PROVIDER,
            "max_tokens": 8192,
            "system_instruction_supported": True,
        },
    }

    def __init__(self):
        self.enabled = bool(os.environ.get("VERTEX_AI_PROJECT_ID", ""))
        if self.enabled:
            vertexai.init(
                project=os.environ.get("VERTEX_AI_PROJECT_ID"),
                location=os.environ.get("VERTEX_AI_LOCATION"),
            )

    def set_model(self, model_name: str):
        if model_name not in self.MODELS.keys():
            raise ValueError("Invalid model")
        self.current_model = model_name

    def get_models(self) -> dict:
        if self.enabled:
            return self.MODELS
        else:
            return {}

    def generate_response(self, prompt: str, system_content: str) -> str:
        logger.info(f"[VertexAI] Generating response with model: {self.current_model}")
        logger.info(f"[VertexAI] Enabled: {self.enabled}")
        logger.info(f"[VertexAI] Prompt length: {len(prompt)}")
        logger.info(f"[VertexAI] System content length: {len(system_content)}")
        
        system_instruction = None
        if self.MODELS[self.current_model]["system_instruction_supported"]:
            system_instruction = system_content
            logger.info(f"[VertexAI] Using system instruction")
        else:
            prompt = system_content + "\n" + prompt
            logger.info(f"[VertexAI] Prepending system content to prompt")

        try:
            logger.info(f"[VertexAI] Initializing GenerativeModel...")
            self.client = vertexai.generative_models.GenerativeModel(
                model_name=self.current_model,
                generation_config={
                    "max_output_tokens": self.MODELS[self.current_model]["max_tokens"],
                },
                system_instruction=system_instruction,
            )
            
            logger.info(f"[VertexAI] Making API request...")
            logger.debug(f"[VertexAI] Prompt: {prompt[:200]}...")
            
            response = self.client.generate_content(
                contents=prompt,
            )
            
            logger.info(f"[VertexAI] API request successful!")
            logger.info(f"[VertexAI] Response type: {type(response)}")
            logger.debug(f"[VertexAI] Response object: {response}")
            
            result = "".join(part.text for part in response.candidates[0].content.parts)
            logger.info(f"[VertexAI] Output text length: {len(result)}")
            logger.debug(f"[VertexAI] Output text preview: {result[:200]}...")
            
            return result

        except google.api_core.exceptions.Unauthorized as e:
            logger.error(f"[VertexAI] Client is not Authorized. {e.reason}, {e.message}", exc_info=True)
            raise e
        except google.api_core.exceptions.Forbidden as e:
            logger.error(f"[VertexAI] Client Forbidden. {e.reason}, {e.message}", exc_info=True)
            raise e
        except google.api_core.exceptions.TooManyRequests as e:
            logger.error(f"[VertexAI] Too many requests. {e.reason}, {e.message}", exc_info=True)
            raise e
        except google.api_core.exceptions.ClientError as e:
            logger.error(f"[VertexAI] Client error: {e.reason}, {e.message}", exc_info=True)
            raise e
        except google.api_core.exceptions.ServerError as e:
            logger.error(f"[VertexAI] Server error: {e.reason}, {e.message}", exc_info=True)
            raise e
        except google.api_core.exceptions.GoogleAPICallError as e:
            logger.error(f"[VertexAI] Error: {e.reason}, {e.message}", exc_info=True)
            raise e
        except google.api_core.exceptions.GoogleAPIError as e:
            logger.error(f"[VertexAI] Unknown error. {e}", exc_info=True)
            raise e
        except Exception as e:
            logger.error(f"[VertexAI] Unexpected error: {type(e).__name__}: {str(e)}", exc_info=True)
            raise e
