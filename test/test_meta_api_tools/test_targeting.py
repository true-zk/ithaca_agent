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
from ithaca.tools.meta_api.meta_ads_targeting import (
    search_interests,
    get_interests_suggestions,
    search_behaviors,
    search_demographics,
    search_geo_locations,
    estimate_audience_size,
)


def test_search_interests():
    print("=" * 60)
    print("Testing search interests tool")
    print("=" * 60)
    res = asyncio.run(search_interests("sports"))
    print(json.dumps(res, indent=2))


def test_estimate_audience_size():
    print("=" * 60)
    print("Testing estimate audience size tool")
    print("=" * 60)
    res = asyncio.run(estimate_audience_size("act_368401904774563", {
        "geo_locations": {"countries": ["US"]},
        # "interests": ["sports"],
    }))
    print(json.dumps(res, indent=2))


# test_search_interests()
test_estimate_audience_size()
