"""
Holistic Agent is provided all tools and complete the task in a holistic way.
This is end-to-end agent.
We only track its tool calls and final outputs.

Task: sreach the product and history (if any), then create a marketing plan for the product, then execute the marketing plan.
Output: marketing plans.
"""
from typing import Optional, Dict, Any, List, Generator
import json
from datetime import datetime

from langchain.agents import create_agent
from ithaca.llms.base import BaseLLM
from langchain.agents.middleware import LLMToolSelectorMiddleware, TodoListMiddleware, SummarizationMiddleware

from ithaca.llms.gemini import gemini_llm
from ithaca.logger import logger
from ithaca.db import IthacaDB, HistoryModel
from ithaca.agents.agent_types import HolisticInput, HolisticOutput, HistoryMarketingPlan


SYSTEM_PROMPT = """
You are a holistic Meta Ads marketing agent.
You will be given a product, and optional marketing history, your task is to:
- searching the product, market, and marketing history (if any)
- creating 3-5 Meta Ads marketing plans for the product
- each plan should contain detailed description and structured tool calls
- executing the marketing plans
- output the marketing plans in the specified JSON format

Example output of a marketing plan with tool calls:
{
    "plan_uuid": "uuid-here",
    "plan_name": "Awareness Campaign",
    "plan_description": "Create a brand awareness campaign targeting fitness enthusiasts",
    "plan_details": "... I will use the create_adset tool "
}

Available Tools:
- web_summary: to summarize the content of a web page
- random_uuid: to generate a random UUID
- common_api_call_tool: to call any Meta Ads API
- get_ad_accounts: to get user's ad accounts
- get_ad_account_info: to get information about a specific ad account
- get_pages_for_account: to get pages for a specific ad account
- search_pages_by_name: to search pages by name
- get_campaigns: to get campaigns for a specific ad account
- get_campaign_details: to get details about a specific campaign
- create_campaign: to create a new campaign
- update_campaign: to update a campaign
- delete_campaign: to delete a campaign
- unassociate_campaign: to unassociate a campaign from an ad account
- get_adsets: to get adsets for a specific campaign
- get_adset_details: to get details about a specific adset
- create_adset: to create a new adset
- update_adset: to update an adset
- delete_adset: to delete an adset
- get_ads: to get ads for a specific adset, campaign, or ad account
- get_ad_details: to get details about a specific ad
- create_ad: to create a new ad
- update_ad: to update an ad
- delete_ad: to delete an ad
- get_creative_by_account: to get creatives for a specific ad account
- get_creatives_by_ad: to get creatives for a specific ad
- get_creative_details: to get details about a specific creative
- create_creative: to create a new creative
- update_creative: to update a creative
- delete_creative: to delete a creative
- get_ad_image: to get the image for a specific ad
- upload_ad_image: to upload an image for a specific ad
- search_interests: to search interests
- get_interests_suggestions: to get interests suggestions
- search_behaviors: to search behaviors
- search_demographics: to search demographics
- search_geo_locations: to search geo locations
- estimate_audience_size: to estimate audience size
- create_budget_schedule: to create a budget schedule

Make sure each marketing plan includes specific, actionable tool calls that follow the exact format specified above.
"""


class HolisticAgent:
    """
    Holistic marketing agent class
    """
    def __init__(
        self,
        llm: Optional[BaseLLM] = None,
        tool_selector_model: Optional[BaseLLM] = None,
        tool_selector_max_tools: int = 10,
        tool_selector_always_include: List[str] = ["random_uuid", "common_api_call_tool"],
        summarization_enabled: bool = True,
        summarization_model: Optional[BaseLLM] = None,
        summarization_max_tokens_before_summary: int = 2048,
    ):
        self.llm = llm or gemini_llm.get_langchain_llm()

        self.tool_selector_model = tool_selector_model or gemini_llm.get_langchain_llm()
        self.tool_selector_max_tools = tool_selector_max_tools
        self.tool_selector_always_include = tool_selector_always_include

        self.summarization_enabled = summarization_enabled
        self.summarization_model = summarization_model or gemini_llm.get_langchain_llm()
        self.summarization_max_tokens_before_summary = summarization_max_tokens_before_summary

        self.agent = self._create_agent()
        logger.info(f"Holistic agent created with args: {self.__dict__}")

    def _create_agent(self):
        """
        Create a holistic marketing agent with structured output constraints.
        """
        # Import all available tools
        from ithaca.tools import (
            web_summary, random_uuid, get_ad_accounts, get_ad_account_info,
            get_pages_for_account, search_pages_by_name, get_campaigns,
            get_campaign_details, create_campaign, update_campaign, delete_campaign,
            unassociate_campaign, get_adsets, get_adset_details, create_adset,
            update_adset, delete_adset, get_ads, get_ad_details, create_ad,
            update_ad, delete_ad, get_creative_by_account, get_creatives_by_ad,
            get_creative_details, create_creative, update_creative, delete_creative,
            get_ad_image, upload_ad_image, search_interests, get_interests_suggestions,
            search_behaviors, search_demographics, search_geo_locations,
            estimate_audience_size, create_budget_schedule
        )
        
        tools = [
            web_summary, random_uuid, get_ad_accounts, get_ad_account_info,
            get_pages_for_account, search_pages_by_name, get_campaigns,
            get_campaign_details, create_campaign, update_campaign, delete_campaign,
            unassociate_campaign, get_adsets, get_adset_details, create_adset,
            update_adset, delete_adset, get_ads, get_ad_details, create_ad,
            update_ad, delete_ad, get_creative_by_account, get_creatives_by_ad,
            get_creative_details, create_creative, update_creative, delete_creative,
            get_ad_image, upload_ad_image, search_interests, get_interests_suggestions,
            search_behaviors, search_demographics, search_geo_locations,
            estimate_audience_size, create_budget_schedule
        ]
        
        middleware = [
            TodoListMiddleware(),
            # There are too many tools, so we need to dynamically select the tools to use.
            LLMToolSelectorMiddleware(
                model=self.tool_selector_model,
                max_tools=self.tool_selector_max_tools,
                always_include=self.tool_selector_always_include
            )
        ]
        if self.summarization_enabled:
            middleware.append(SummarizationMiddleware(
                model=self.summarization_model,
                max_tokens_before_summary=self.summarization_max_tokens_before_summary,
            ))
        
        # Create the agent
        agent = create_agent(
            model=self.llm,
            tools=tools,
            system_prompt=SYSTEM_PROMPT,
            middleware=middleware,
            response_format=HolisticOutput,
        )
        
        return agent
    
    def _extract_latest5_hist_from_db(self, product_name: str, product_url: str) -> List[HistoryMarketingPlan]:
        q_res = IthacaDB.advanced_query(
            HistoryModel,
            filters={"product_name": product_name, "product_url": product_url},
            order_by="created_at",
            order_desc=True,
            limit=5
        )
        return q_res
    
    def _init_prompt(self, input: HolisticInput) -> str:
        """
        Run with noval product, i.e. without history.
        """
        prompt = """
        You are first time to market the product {product_name} with url {product_url}.
        The optional product picture is {product_picture_url}.
        {budget_prompt}

        Please:
        1. research the product, 
        2. create 3-5 marketing plans for the product, each plan should contain detailed description and structured tool calls,
        3. execute the marketing plans,
        4. output the marketing plans in the specified JSON format.
        """
        if input.total_budget is not None:
            budget_prompt = f"The total budget is {input.total_budget}. The sum of budgets of all marketing plans should be less than or equal to the total budget."
        else:
            budget_prompt = "The total budget is not provided should call tool to get the total budget."

        return prompt.format(
            product_name=input.product_name,
            product_url=input.product_url,
            product_picture_url=input.product_picture_url or "not provided",
            budget_prompt=budget_prompt
        )
    
    def _loop_prompt(self, input: HolisticInput) -> str:
        """
        Run with history.
        """
        prompt = """
        You are already marketing the product {product_name} with url {product_url}.
        The optional product picture is {product_picture_url}.
        {budget_prompt}

        The marketing history is:
        {marketing_history}

        Please:
        1. research the product, and marketing history
        2. based on the research, created 1-2 new and better marketing plans,
        3. execute the new marketing plans
        4. output the updated marketing plans in the specified JSON format.
        """
        if input.total_budget is not None:
            budget_prompt = f"The total budget is {input.total_budget}. The sum of budgets of all marketing plans should be less than or equal to the total budget."
        else:
            budget_prompt = "The total budget is not provided should call tool to get the total budget."

        return prompt.format(
            product_name=input.product_name,
            product_url=input.product_url,
            product_picture_url=input.product_picture_url or "not provided",    
            budget_prompt=budget_prompt,
            marketing_history=json.dumps(input.marketing_history, indent=2)
        )

    def get_prompt(self, input: HolisticInput) -> str:
        """
        Get the prompt for the holistic agent.
        """
        assert input.product_name is not None and input.product_url is not None

        if input.product_picture_url is None:
            logger.warning(f"Product picture url is not provided.")
        
        if input.marketing_history is None or len(input.marketing_history) == 0:
            # try to extract from db
            input.marketing_history = self._extract_latest5_hist_from_db(input.product_name, input.product_url)

        return self._loop_prompt(input) if input.marketing_history is not None and len(input.marketing_history) > 0 else self._init_prompt(input)
    
    def _parse_response(self, response: Dict[str, Any]) -> HolisticOutput:
        """
        Parse the response from the holistic agent.
        """
        try:
            output = HolisticOutput.model_validate_json(response["structured_output"])
            for plan in output.marketing_plans:
                plan.created_at = datetime.now()
            return output
        except Exception as e:
            logger.error(f"Error parsing response: {e}")
            logger.error(f"Response: {response["structured_output"]}")
            return None

    def run(self, input: HolisticInput) -> Dict[str, Any]:
        """
        Run the holistic agent.
        """
        response = self.agent.invoke(
            {"messages": [
                {"role": "user", "content": self.get_prompt(input)}
            ]}
        )
        output = {
            "response": response,
            "parsed_output": self._parse_response(response)
        }
        return output

    async def run_async(self, input: HolisticInput) -> Dict[str, Any]:
        """
        Run the holistic agent asynchronously.
        """
        response = await self.agent.ainvoke(
            {"messages": [
                {"role": "user", "content": self.get_prompt(input)}
            ]}
        )
        output = {
            "response": response,
            "parsed_output": self._parse_response(response)
        }
        return output

    def run_stream(self, input: HolisticInput, stream_mode: str = "values") -> Generator[str, None, None]:
        """
        Run the holistic agent streamingly.
        """
        final_output= None

        for chunk in self.agent.stream(
            {"messages": [
                {"role": "user", "content": self.get_prompt(input)}
            ]},
            stream_mode=stream_mode
        ):
            yield chunk

            if "structured_output" in chunk:
                tmp_output = self._parse_response(chunk)
                if tmp_output is not None:
                    final_output = tmp_output

        return final_output
        
