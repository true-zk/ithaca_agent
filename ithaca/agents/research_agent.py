"""
Research agent
"""
from typing import List, Callable, Dict, Any, Optional
from pydantic import BaseModel, Field

from google.genai import types

from ithaca.agents.base import BaseAgent
from ithaca.logger import logger


class ResearchAgentInput(BaseModel):
    product_name: str
    product_url: str
    picture_urls: List[str]
    additional_data: Optional[str] = None


class ResearchAgentOutput(BaseModel):
    picture_urls: List[str]
    keywords: List[str]
    research_summary: str


class ResearchAgent(BaseAgent):
    def __init__(
        self,
        name: str = "ResearchAgent",
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

    
    def _build_prompt(self, input: ResearchAgentInput) -> str:
        prompt = f"""
        User want to create a marketing plan for the product {input.product_name}.
        You are a research agent.
        You are given the following information:
            - Product name: {input.product_name}
            - Product url: {input.product_url}
            - Product picture urls: {input.picture_urls}
            - Addtional info provided by the user (Optional):
            {input.additional_data}

        You are tasked with researching the product using the tools provided, and:
            1. Find the keywords related to the product
            2. Summarize the research of the product:
                - The product background
                - The product features
                - Suggestions for the marketing plan
                - Any other relevant information
            3. Find other accessible better product picture urls if possible 
                (make sure the pictures are useful and can be downloaded from the url)
        
        IMPORTANT: Your research result will be used by the next agent
        to generate a marketing plan. You should research following this goal.
        """
        prompt += """
        You should returen in a json format like:
        {
            "picture_urls": List[str] ["Product picture urls adding the new found picture urls"],
            "keywords": List[str] ["Keywords"],
            "research_summary": str "Research summary"
        }
        """
        return prompt

    def run(self, input: ResearchAgentInput) -> Dict[str, Any]:
        prompt = self._build_prompt(input)
        schema = ResearchAgentOutput.model_json_schema()
        try:
            res = self._generate_once(
                prompt=prompt,
                schema=schema
            )
            res = ResearchAgentOutput.model_validate(res)
            context = {
                "messages": [
                    {
                        "instruction": prompt,
                        "response": res.model_dump_json()
                    }
                ]
            }
            cache_file = self._cache_context(context)
            logger.info(f"[ResearchAgent] Cached context to {cache_file}")
            return res.model_dump()
        except Exception as e:
            logger.error(f"[ResearchAgent] Error running research agent: {e}")
            raise e