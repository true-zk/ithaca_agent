import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from ithaca.oauth.auth import auth_manager
from ithaca.tools.meta_api import get_ad_accounts
from ithaca.llms.gemini import GeminiLLM


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

def test_llm_toolcall():
    """Test LLM tool call"""
    print("=" * 60)
    print("Testing LLM tool call")
    print("=" * 60)
    
    llm = GeminiLLM()
    agent = pass
    print(res)

test_get_ad_accounts()