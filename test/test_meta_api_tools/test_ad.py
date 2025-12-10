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

# Test tools
from ithaca.tools.meta_api.meta_ads_ad import (
    get_ads,
    get_ad_details,
    create_ad,
    update_ad,
    delete_ad,
)


def test_get_ads():
    print("=" * 60)
    print("Testing get ads tool")
    print("=" * 60)
    res = asyncio.run(get_ads.ainvoke({
        # "account_id": "act_368401904774563",
        # "campaign_id": "120237264670600156",
        "adset_id": "120237344008200156",
    }))
    print(json.dumps(res, indent=2, ensure_ascii=False))


def test_get_ad_details():
    print("=" * 60)
    print("Testing get ad details tool")
    print("=" * 60)
    res = asyncio.run(get_ad_details.ainvoke({
        "ad_id": "120237264817810156",
    }))
    print(json.dumps(res, indent=2, ensure_ascii=False))

def test_create_ad():
    print("=" * 60)
    print("Testing create ad tool")
    print("=" * 60)
    res = asyncio.run(create_ad.ainvoke({
        "account_id": "act_368401904774563",
        "adset_id": "120237344008200156",
        "ad_name": "multi pic abab Test Ad AAAA",
        "bid_amount": 100,
        "creative_id": "1550228496180500",  # dynamic creative
    }))
    print(json.dumps(res, indent=2, ensure_ascii=False))


def test_update_ad():
    print("=" * 60)
    print("Testing update ad tool")
    print("=" * 60)
    res = asyncio.run(update_ad.ainvoke({
        "ad_id": "120237362878130156",
        "creative_id": "1581322583040540",
        "bid_amount": 101,
    }))
    print(json.dumps(res, indent=2, ensure_ascii=False))


# test_get_ads()
# test_get_ad_details()
# test_create_ad()
test_update_ad()