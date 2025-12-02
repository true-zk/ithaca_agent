"""
Evaluation Agent is isolated agent that is responsible for evaluating the performance of a group of marketing plans.
After evaluation, it will give a score and summary of each marketing plan, and update the history.
"""
from typing import Optional, Dict, Any, List, Generator
import json
from datetime import datetime

from langchain.agents import create_agent
from ithaca.llms.base import BaseLLM
from langchain.agents.middleware import LLMToolSelectorMiddleware, TodoListMiddleware, SummarizationMiddleware
from deepagents import create_deep_agent

from ithaca.llms.gemini import gemini_llm
from ithaca.logger import logger
from ithaca.db import IthacaDB, HistoryModel
from ithaca.agents.agent_types import EvaluationInput, EvaluationOutput, HistoryMarketingPlan
from ithaca.tools.meta_api import update_ad


SYSTEM_PROMPT = """
You are a marketing evaluation agent.
You are responsible for evaluating the performance of The new marketing plan.
After evaluation, you will give a score and summary of the new marketing plan.

Available Tools:
- common_api_call_tool: to call any Meta Ads API
- get_insights: to get performance insights for a Meta Ads 'campaign', 'ad set', 'ad' or 'account'.
- get_ad_accounts: to get user's ad accounts
- get_ad_account_info: to get information about a specific ad account
- get_pages_for_account: to get pages for a specific ad account
- get_campaigns: to get campaigns for a specific ad account
- get_campaign_details: to get details about a specific campaign
- get_adsets: to get adsets for a specific campaign
- get_adset_details: to get details about a specific adset
- get_ads: to get ads for a specific adset, campaign, or ad account
- get_ad_details: to get details about a specific ad
- update_campaign: to update a specific campaign
- delete_campaign: to delete a specific campaign
- delete_adset: to delete a specific adset
- delete_ad: to delete a specific ad
- update_adset: to update a specific adset
- update_ad: to update a specific ad
"""


class EvaluationAgent:
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

        self.tool_selector_model = tool_selector_model or gemini_llm.get_tool_selector_model()
        self.tool_selector_max_tools = tool_selector_max_tools
        self.tool_selector_always_include = tool_selector_always_include

        self.summarization_enabled = summarization_enabled
        self.summarization_model = summarization_model or gemini_llm.get_langchain_llm()
        self.summarization_max_tokens_before_summary = summarization_max_tokens_before_summary

        self.agent = self._create_agent()

    def _create_agent(self):
        """
        Create a evaluation agent with structured output constraints.
        """
        from ithaca.tools import (
            common_api_call_tool, get_insights, get_ad_accounts, get_ad_account_info,
            get_pages_for_account, get_campaigns, get_campaign_details, get_adsets, get_adset_details, get_ads, get_ad_details,
            update_campaign, delete_campaign, delete_adset, delete_ad, update_adset, update_ad
        )

        tools = [
            common_api_call_tool, get_insights, get_ad_accounts, get_ad_account_info,
            get_pages_for_account, get_campaigns, get_campaign_details, get_adsets, get_adset_details, get_ads, get_ad_details,
            update_campaign, delete_campaign, delete_adset, delete_ad, update_adset, update_ad
        ]

        middleware = []
        if self.summarization_enabled:
            middleware.append(SummarizationMiddleware(
                model=self.summarization_model,
                max_tokens_before_summary=self.summarization_max_tokens_before_summary,
            ))
        
        # Create the agent
        # agent = create_agent(
        #     model=self.llm,
        #     tools=tools,
        #     system_prompt=SYSTEM_PROMPT,
        #     # middleware=middleware,
        #     response_format=EvaluationOutput,
        # )
        agent = create_deep_agent(
            model=self.llm,
            tools=tools,
            system_prompt=SYSTEM_PROMPT,
            # middleware=middleware,
            response_format=HistoryMarketingPlan,
        )
        return agent
    
    def get_prompt(self, input: EvaluationInput) -> str:
        """
        Get the prompt for the evaluation agent.
        """
        if input.history_marketing_plans is None:
            input.history_marketing_plans = HistoryMarketingPlan.extract_latest5_hist_from_db(
                input.product_name,
                input.product_url
            )
        prompt = f"""
        The product being marketed is {input.product_name} with url {input.product_url}.
        The total budget for the new marketing plans is {input.total_budget}.

        You are evaluating the performance of the following new marketing plans:
        {json.dumps(input.new_marketing_plans, indent=2)}

        The history marketing plans are (this is for reference only):
        {json.dumps(input.history_marketing_plans, indent=2)}

        Please:
        1. calculate the actual cost and evaluate the performance of each marketing plan compared with the history marketing plans
        2. give a score and summary of each marketing plan (float from 1 to 10) 
        3. stop or delete the Meta Ads campaigns / adsets / ads according to the current marketing plans. 
            And make sure there is no running Meta Ads campaigns.
        4. output the evaluation results in the specified JSON format.
        """
        return prompt
    
    def _parse_response(self, input: EvaluationInput, response: Dict[str, Any]) -> Optional[EvaluationOutput]:
        """
        Parse the response from the evaluation agent.
        """
        try:
            marketing_plan = None
            plan: Optional[Dict[str, Any]] = response["structured_response"]
            if plan is None:
                logger.error("Marketing plan not found")
                return None
            
            marketing_plan = HistoryMarketingPlan(
                plan_uuid=plan.get("plan_uuid", ""),
                plan_description=plan.get("plan_description", ""),
                plan_details=plan.get("plan_details", ""),
                budget=plan.get("budget", 0),
                actual_cost=plan.get("actual_cost", 0),
            )
            
            return EvaluationOutput(
                product_name=input.product_name,
                product_url=input.product_url,
                marketing_plan=marketing_plan,
            )
        except Exception as e:
            logger.error(f"Error parsing response: {e}")
            logger.error(f"Response: {response}")
            return None
    
    async def run(self, input: EvaluationInput) -> Dict[str, Any]:
        """
        Run the evaluation agent.
        """
        response = await self.agent.ainvoke(
            {"messages": [
                {"role": "user", "content": self.get_prompt(input)}
            ]}
        )
        output = {
            "response": response,
            # "parsed_output": self._parse_response(response)
        }
        return output
    