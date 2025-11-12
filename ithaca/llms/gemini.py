"""
Gemini LLM client
"""
from typing import Optional, List, Dict, Any, Union
import os

import google.genai as genai

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

    def generate(
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
        