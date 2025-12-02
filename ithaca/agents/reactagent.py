from typing import Optional, Dict, Any, List, Generator
import json
from datetime import datetime

from deepagents import create_deep_agent
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents.middleware import LLMToolSelectorMiddleware

from ithaca.llms.base import BaseLLM
from ithaca.llms.gemini import gemini_llm
from ithaca.logger import logger


SYSTEM_PROMPT = """
You are a holistic Meta Ads marketing agent with long-term memory.
You will be given a product, and optional marketing history, 
and you should follow the user's request to complete the task.

TOOLUSAGE:
If you find some arguments are not clear, you should call other tools to get them.
e.g. if you need adaccount_id, you should call get_ad_accounts tool to get it.

IMPORTANT: You have access to the complete conversation history in your current thread/session.
- All previous messages in this conversation are available to you
- You can refer back to anything mentioned earlier in this conversation
- You should use this context to provide better responses

When a user asks about something from earlier in the conversation:
1. Look through the conversation history (which is provided to you)
2. Reference what was discussed before
3. Build upon previous context
"""


TOOL_SELECTOR_SYSTEM_PROMPT = """
You are a tool selector.
Select the most useful tools to use based on the user's request.

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
"""

from deepagents.backends import CompositeBackend, StateBackend, StoreBackend
from langgraph.store.memory import InMemoryStore

def make_backend(runtime):
    return CompositeBackend(
        default=StateBackend(runtime),  # Ephemeral storage
        routes={
            "/memories/": StoreBackend(runtime)  # Persistent storage
        }
    )


class ReactAgent:
    """
    React agent class
    """
    def __init__(
        self,
        llm: Optional[BaseLLM] = None,
        tool_selector_model: Optional[BaseLLM] = None,
        tool_selector_max_tools: int = 10,
        tool_selector_always_include: List[str] = ["random_uuid", "common_api_call_tool"],
    ):
        self.llm = llm or gemini_llm.get_langchain_llm(max_tokens=8192)

        self.tool_selector_model = tool_selector_model or gemini_llm.get_langchain_llm()
        self.tool_selector_max_tools = tool_selector_max_tools
        self.tool_selector_always_include = tool_selector_always_include

        self.agent = self._create_agent()
        logger.info(f"React agent created with args: {self.__dict__}")

    def _create_agent(self):
        """
        Create a react agent with structured output constraints.
        """
        # Import all available tools
        from ithaca.tools import (
            web_summary, random_uuid, common_api_call_tool, get_ad_accounts, get_ad_account_info,
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
        from ithaca.tools import web_search
        
        tools = [
            web_summary, web_search, random_uuid, common_api_call_tool, get_ad_accounts, get_ad_account_info,
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

        middleware = []
        middleware.append(LLMToolSelectorMiddleware(
            model=self.tool_selector_model,
            system_prompt=TOOL_SELECTOR_SYSTEM_PROMPT,
            max_tools=self.tool_selector_max_tools,
            always_include=self.tool_selector_always_include,
        ))
        
        agent = create_deep_agent(
            model=self.llm,
            tools=tools,
            system_prompt=SYSTEM_PROMPT,
            checkpointer=InMemorySaver(),
            store=InMemoryStore(),
            backend=make_backend,
            middleware=middleware,
        )
        
        return agent
        
