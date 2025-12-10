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
from ithaca.tools.meta_api.meta_ads_page import get_pages_for_account_tool, get_pages_by_name_tool


def test_get_pages_for_account():
    """Test get pages for account tool"""
    print("=" * 60)
    print("Testing get pages for account tool")
    print("=" * 60)
    res = get_pages_for_account_tool("act_368401904774563")
    print(json.dumps(res, indent=2))


def test_search_pages_by_name():
    """Test search pages by name tool"""
    print("=" * 60)
    print("Testing search pages by name tool")
    print("=" * 60)
    res = get_pages_by_name_tool("act_368401904774563", "Facebook")
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    test_get_pages_for_account()
    test_search_pages_by_name()