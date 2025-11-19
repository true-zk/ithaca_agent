import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from ithaca.oauth.auth import auth_manager
from ithaca.llms.gemini import GeminiLLM
from ithaca.subagents.research_agent import research_agent

# auth_manager.authenticate(force_refresh=True)

def get_access_token():
    """Get access token"""
    if not auth_manager.get_access_token():
        auth_manager.authenticate(force_refresh=True)
    return auth_manager.get_access_token()

def test_research_agent():
    """Test research agent"""
    print("=" * 60)
    print("Testing research agent")
    print("=" * 60)
    
    access_token = get_access_token()

    res = asyncio.run(research_agent.ainvoke(
        {"messages": [
            {"role": "user", "content": "What are the ad accounts for the user?"}
        ]}
    ))
    print(res)
    print("=" * 60)
    print(res["messages"][-1].content)


test_research_agent()