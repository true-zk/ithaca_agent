import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from langchain.agents import create_agent

from ithaca.oauth.auth import auth_manager
from ithaca.tools.meta_api import *
from ithaca.llms.gemini import gemini_llm


def get_access_token():
    """Get access token"""
    if not auth_manager.get_access_token():
        auth_manager.authenticate(force_refresh=True)
    return auth_manager.get_access_token()

def test_get_ad_accounts():
    """Test get ad accounts tool"""
    print("=" * 60)
    print("Testing get ad accounts tool")
    print("=" * 60)
    
    access_token = get_access_token()
    res = asyncio.run(get_ad_accounts.ainvoke({"access_token": access_token}))
    print(res)

async def test_llm_toolcall():
    """Test LLM tool call"""
    print("=" * 60)
    print("Testing LLM tool call")
    print("=" * 60)
    
    agent = create_agent(
        model=gemini_llm.get_langchain_llm(),
        tools=[get_ad_accounts, common_api_call_tool],
        system_prompt="You are a tool call test agent."
    )
    prompt = """You are tool call test agent
    please get the ad accounts for the user.
    """
    res = await agent.ainvoke({"messages": [{"role": "user", "content": prompt}]})
    print(res)


# test_get_ad_accounts()
asyncio.run(test_llm_toolcall())