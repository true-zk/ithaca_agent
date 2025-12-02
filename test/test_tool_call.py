import asyncio
import json
import sys
from pathlib import Path
import time
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Dict, Any, List

sys.path.insert(0, str(Path(__file__).parent.parent))

from langchain.agents import create_agent
from langchain.agents.middleware import LLMToolSelectorMiddleware, TodoListMiddleware, SummarizationMiddleware

from ithaca.llms.base import BaseLLM
from ithaca.llms.gemini import gemini_llm
from ithaca.oauth.auth import auth_manager


class ToolCallInfo(BaseModel):
    tool_call_id: str
    tool_name: str = Field(description="The name of the tool to call")
    tool_args: Dict[str, Any] = Field(description="The arguments to pass to the tool")
    tool_result: Any = Field(description="The result of the tool call")


class DummyAgentOutput(BaseModel):
    description: str = Field(description="The description of the output")
    res: List[ToolCallInfo] = Field(description="The list of tool calls")


class DummyAgent:
    def __init__(self):
        self.llm = gemini_llm.get_langchain_llm()

        self.agent = self._create_agent()

    def _create_agent(self):
        """
        Create a holistic marketing agent with structured output constraints.
        """
        # Import all available tools
        from ithaca.tools import (
            web_summary, random_uuid, common_api_call_tool, get_ad_accounts, get_ad_account_info,
            get_pages_for_account, search_pages_by_name, get_campaigns,
            get_campaign_details, get_adsets, get_adset_details,
            get_ads, get_ad_details,
            get_creative_by_account, get_creatives_by_ad,
            get_creative_details,
            get_ad_image, upload_ad_image, search_interests, get_interests_suggestions,
            search_behaviors, search_demographics, search_geo_locations,
            estimate_audience_size
        )
        
        tools = [
            web_summary, random_uuid, common_api_call_tool, get_ad_accounts, get_ad_account_info,
            get_pages_for_account, search_pages_by_name, get_campaigns,
            get_campaign_details, get_adsets, get_adset_details, get_ads, get_ad_details,
            get_creative_by_account, get_creatives_by_ad,
            get_creative_details, 
            get_ad_image, upload_ad_image, search_interests, get_interests_suggestions,
            search_behaviors, search_demographics, search_geo_locations,
            estimate_audience_size
        ]
        
        middleware = [
            # TodoListMiddleware(),
            # There are too many tools, so we need to dynamically select the tools to use.
            LLMToolSelectorMiddleware(
                model=gemini_llm.get_tool_selector_model(),
                system_prompt="""
                You are a tool selector.
                Select the most useful tools to use based on the user's request.
                tools:
                web_summary, random_uuid, common_api_call_tool, get_ad_accounts, get_ad_account_info,
                get_pages_for_account, search_pages_by_name, get_campaigns,
                get_campaign_details, get_adsets, get_adset_details, get_ads, get_ad_details,
                get_creative_by_account, get_creatives_by_ad,
                get_creative_details, 
                get_ad_image, upload_ad_image, search_interests, get_interests_suggestions,
                search_behaviors, search_demographics, search_geo_locations,
                estimate_audience_size
                """,
                max_tools=10,
                # always_include=["random_uuid", "common_api_call_tool"]
            ),
        ]
        
        # Create the agent
        agent = create_agent(
            model=self.llm,
            tools=tools,
            system_prompt="You are a tool call test agent.",
            middleware=middleware,
            response_format=DummyAgentOutput,
        )
        
        return agent

    async def arun(self, prompt: str):
        """
        Run the holistic agent.
        """
        response = await self.agent.ainvoke(
            {"messages": [
                {"role": "user", "content": prompt}
            ]}
        )
        return response


async def test_agent_tool_call():
    if not auth_manager.get_access_token():
        auth_manager.authenticate(force_refresh=True)

    dummyagent = DummyAgent()
    prompt = """You are tool call test agent.
    Please make a plan and test the tools.

    Please get the Meta Ads information for the user.
    Include the ad accounts, campaigns, adsets, ads, creatives, etc.
    If you need any information, please use tools to get the information.
    E.g. get the campaigns need to know the ad accounts first, so you should call get_ad_accounts first.
    """

    print("=" * 20)
    res = await dummyagent.arun(prompt)
    print(res["messages"])
    print(res["structured_response"])


if __name__ == "__main__":
    asyncio.run(test_agent_tool_call())