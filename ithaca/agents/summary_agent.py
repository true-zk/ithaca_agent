"""
Summary agent
"""
from typing import List, Callable, Dict, Any, Optional
from pydantic import BaseModel, Field
import json

from google.genai import types

from ithaca.workflow.data_type import MarketingPlan
from ithaca.agents.base import BaseAgent
from ithaca.logger import logger


class SummaryAgent(BaseAgent):
    def __init__(
        self,
        name: str = "SummaryAgent",
        max_retry: int = 3,
    ):
        model = "gemini-3-pro-preview"  # support schema output with tools
        tools = [
            types.Tool(
                google_search=types.GoogleSearch(),
                url_context=types.UrlContext()
            )
        ]
        super().__init__(name, model, tools=tools, max_retry=max_retry)

    def _build_prompt(self, input: MarketingPlan) -> str:
        prompt = f"""
        The marketing plan is finished. You should summary the marketing plan including the research, plan, update and summary.

        1. You should call tools to get the final insights (performance) of the marketing plan
        2. After that, you should analyze the marketing plan with update logs to give a summary.
        
        You should focus on the performance of the marketing plan at adsets / ads level and
        the effect of the update made by the UpdateAgent.

        Marketing Plan:
        {input.model_dump_json(indent=2)}
        """
        return prompt

    def run(self, input: MarketingPlan) -> str:
        prompt = self._build_prompt(input)
        try:
            res = self._generate_once(
                prompt=prompt,
            )
            context = {
                "messages": [
                    {
                        "instruction": prompt,
                        "response": res
                    }
                ]
            }
            cache_file = self._cache_context(context)
            logger.info(f"[SummaryAgent] Cached context to {cache_file}")
            return res
        except Exception as e:
            logger.error(f"[SummaryAgent] Error running summary agent: {e}")
            raise e