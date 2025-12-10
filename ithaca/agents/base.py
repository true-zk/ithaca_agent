"""
Warp Gemini LLM to agent.

"""
from typing import List, Callable, Optional, Dict, Any, Union
import time
import json
from datetime import datetime

from ithaca.llms import gemini_llm
from ithaca.logger import logger
from ithaca.utils import get_cache_dir


class BaseAgent:
    def __init__(
        self,
        name: str,
        model: str,
        tools: Optional[List[Callable]] = None,
        system_prompt: Optional[str] = None,
        max_retry: int = 3,
    ):
        self.name = name
        self.model = model
        self.tools = tools
        self.system_prompt = system_prompt
        self.max_retry = max_retry
    
    def __str__(self) -> str:
        return (
            f"Agent: {self.name}(model={self.model}, "
            f"tools={self.tools}, "
            f"system_prompt={self.system_prompt}, "
            f"max_retry={self.max_retry})"
        )
    
    def _generate_once(
        self,
        prompt: str,
        schema: Optional[Dict[str, Any]] = None,
        system_prompt: Optional[str] = None,
        tools: Optional[List[Callable]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,   
        **kwargs
    ) -> Union[str, Dict[str, Any]]:
        """Generate text from the LLM"""
        def _validate_schema_output(model: str, tools: Optional[List[Callable]]) -> bool:
            custom_tool = False
            native_tool = False
            if tools and len(tools) > 0:
                for tool in tools:
                    if callable(tool):
                        custom_tool = True
                    elif isinstance(tool, dict):
                        native_tool = True
            
            if custom_tool or (native_tool and model != "gemini-3-pro-preview"):
                return False
            return True
        
        system_prompt = system_prompt or self.system_prompt
        tools = tools or self.tools

        if schema and not _validate_schema_output(self.model, tools):
            raise ValueError(f"Schema output is not supported for {self.model} with custom tools")

        retry_count = self.max_retry
        if "max_retry" in kwargs:
            retry_count = kwargs["max_retry"]
            kwargs.pop("max_retry")
    
        while True:
            try:
                if schema:
                    return gemini_llm.generate_json(
                        prompt=prompt,
                        schema=schema,
                        model=self.model,
                        system_prompt=system_prompt,
                        tools=tools,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        **kwargs
                    )
                else:
                    return gemini_llm.generate(
                        model=self.model,
                        prompt=prompt,
                        system_prompt=system_prompt,
                        tools=tools,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        **kwargs
                    )
            except Exception as e:
                time.sleep(1)
                if retry_count > 0:
                    logger.warning(f"Error generating response from {self.model}: {e}. Retrying... ({retry_count} retries left)")
                    retry_count -= 1
                    prompt = prompt + "\n\n" + "Error: " + str(e) + ". Please try again."
                    continue
                else:
                    raise Exception(f"Failed to generate response from {self.model} after {self.max_retry} retries")

    # Default context dumper
    def _dumps_context(self, context: Dict[str, Any]) -> str:
        """
        Example:
            >>> context = {"ad_account_id": "1234567890", "campaign_id": ["1234567890", "1234567890"]}
            >>> formatted = agent._format_context(context)
            >>> print(formatted)
            Context:

            AD_ACCOUNT_ID: 1234567890

            CAMPAIGN_ID:
              - 1234567890
              - 1234567890
        """
        context_str = "Context:\n"
        
        for key, value in context.items():
            if isinstance(value, dict):
                context_str += f"\n{key.upper()}:\n"
                for k, v in value.items():
                    context_str += f"  {k}: {v}\n"
            elif isinstance(value, list):
                context_str += f"\n{key.upper()}:\n"
                for item in value:
                    if isinstance(item, dict):
                        for k, v in item.items():
                            context_str += f"  {k}: {v}\n"
                        context_str += "\n"
                    else:
                        context_str += f"  - {item}\n"
            else:
                context_str += f"\n{key.upper()}: {value}\n"
        
        return context_str 

    def _cache_context(self, context: Dict[str, Any]) -> str:
        """
        Caches the context to the cache directory in json format.
        """
        cache_dir = get_cache_dir() / "agent_context"
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = cache_dir / f"{self.name}_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
        cache_file.write_text(json.dumps(context))
        return str(cache_file)