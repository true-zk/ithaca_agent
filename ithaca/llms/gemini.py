"""
Gemini LLM client
"""
from typing import Optional, List, Dict, Any, Union
import os
import json

from google import genai
from google.genai.types import GenerateContentConfig

from ithaca.llms.base import BaseLLM
from ithaca.settings import GEMINI_API_KEY
from ithaca.logger import logger


class GeminiLLM(BaseLLM):
    """
    Gemini LLM client
    """
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gemini-2.5-flash",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        embedding_model: str = "gemini-embedding-001",
        time_out: int = 60
    ):
        """
        Initialize the Gemini LLM client
        """
        self.api_key = api_key or GEMINI_API_KEY or os.getenv("GEMINI_API_KEY")
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.embedding_model = embedding_model
        self.time_out = time_out

        self.client = genai.Client(api_key=self.api_key)

        logger.info(f"Gemini LLM client initialized with model: {self.model}")
        logger.info(f"Temperature: {self.temperature}")
        logger.info(f"Max tokens: {self.max_tokens}")
        logger.info(f"Embedding model: {self.embedding_model}")
        logger.info(f"Time out: {self.time_out}")

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stop_sequences: Optional[List[str]] = None,
        **kwargs
    ) -> str:
        """
        Generate text from the LLM
        """
        temperature = temperature or self.temperature
        max_tokens = max_tokens or self.max_tokens
        
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                    stop_sequences=stop_sequences,
                    tools=kwargs.get("tools", [])
                )
            )
            return response.text
        except Exception as e:
            logger.error(f"Error generating reponse from Gemini: {e}")
            raise e

    async def generate_json(
        self,
        prompt: str,
        schema: Dict[str, Any],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stop_sequences: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate JSON from the LLM
        """
        if kwargs.get("tools"):
            logger.warning(f"Tools are not supported for JSON generation. Ignoring tools {kwargs.get('tools')}.")

        temperature = temperature or self.temperature
        max_tokens = max_tokens or self.max_tokens
        config = GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=temperature,
            max_output_tokens=max_tokens,
            stop_sequences=stop_sequences,
            response_mime_type="application/json",
            response_schema=schema
        )
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=config
            )
            return json.loads(response.text)
        except Exception as e:
            logger.error(f"Error generating JSON from Gemini: {e}")
            raise e

    async def generate_embedding(
        self,
        text: Union[str, List[str]],
        **kwargs
    ) -> Union[List[float], List[List[float]]]:
        """
        Generate embedding from the LLM
        """
        try:
            response = self.client.models.embed_content(
                model=self.embedding_model,
                contents=text
            )
            return response.embeddings
        except Exception as e:
            logger.error(f"Error generating embedding from Gemini: {e}")
            raise e
