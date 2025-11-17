"""
Base LLM client
"""
from typing import Optional, List, Dict, Any, Union
from abc import ABC, abstractmethod


class BaseLLM(ABC):
    """
    Base class for LLM clients.

    LLM clients should implement the following methods:
    - generate
    - generate_json
    - generate_embedding
    """
    @abstractmethod
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
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
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
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    async def generate_embedding(
        self,
        text: Union[str, List[str]],
        **kwargs
    ) -> Union[List[float], List[List[float]]]:
        """
        Generate embedding from the LLM
        """
        raise NotImplementedError("Subclasses must implement this method")