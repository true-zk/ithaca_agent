import sys
from pathlib import Path
import asyncio
import json

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ithaca.oauth.auth import auth_manager

if not auth_manager.get_access_token():
    auth_manager.authenticate(force_refresh=True)

# Test tools
from ithaca.tools.meta_api.meta_ads_adaccount import get_ad_accounts_tool, get_ad_account_info_tool


def test_get_ad_accounts():
    """Test get ad accounts tool"""
    print("=" * 60)
    print("Testing get ad accounts tool")
    print("=" * 60)
    res = get_ad_accounts_tool()
    print(json.dumps(res, indent=2))


def test_get_ad_account_info():
    """Test get ad account info tool"""
    print("=" * 60)
    print("Testing get ad account info tool")
    print("=" * 60)
    res = get_ad_account_info_tool("act_368401904774563")
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    test_get_ad_accounts()
    test_get_ad_account_info()