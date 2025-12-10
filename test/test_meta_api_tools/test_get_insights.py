import sys
from pathlib import Path
import asyncio
import json
import time

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ithaca.oauth.auth import auth_manager

if not auth_manager.get_access_token():
    auth_manager.authenticate(force_refresh=True)
else:
    print(f"Using access token: {auth_manager.get_access_token()[:10]}...")

from ithaca.tools.meta_api.meta_ads_insights import get_insights_tool


# no data
def test_get_insights():
    print("=" * 60)
    print("Testing get insights tool")
    print("=" * 60)
    res = get_insights_tool(
        # id="120237596857910156",
        id="act_368401904774563",
        # time_range="last_30d",
    )
    print(json.dumps(res, indent=2, ensure_ascii=False))


test_get_insights()