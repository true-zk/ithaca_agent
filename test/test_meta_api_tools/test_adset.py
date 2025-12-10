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
from ithaca.tools.meta_api.meta_ads_adset import (
    get_adsets,
    get_adset_details,
    create_adset_tool,
    update_adset,
    delete_adset,
)


def test_get_adsets():
    print("=" * 60)
    print("Testing get ad sets tool")
    print("=" * 60)
    res = asyncio.run(get_adsets.ainvoke({
        "account_id": "act_368401904774563",
        "campaign_id": "120237324123260156",    # AAA test campaign, Objective: OUTCOME_TRAFFIC
    }))
    print(json.dumps(res, indent=2, ensure_ascii=False))


def test_get_adset_details():
    print("=" * 60)
    print("Testing get ad set details tool")
    print("=" * 60)
    res = asyncio.run(get_adset_details.ainvoke({
        "adset_id": "120237344008200156",
    }))
    print(json.dumps(res, indent=2, ensure_ascii=False))


def get_create_adset_config(config_type: str = "default"):
    """Get create ad set config"""
    if config_type == "default":
        return {
            "account_id": "act_368401904774563",
            "campaign_id": "120237324123260156",    # AAA test campaign, Objective: OUTCOME_TRAFFIC
            "adset_name": "AAA Test Ad Set for OUTCOME_TRAFFIC",
            "optimization_goal": "LINK_CLICKS",  
            "billing_event": "IMPRESSIONS",
            "status": "PAUSED",
        }
    elif config_type == "app":  # BUG: "应用程序与给定对象商店的网址不一致。请检查应用程序的配置：https://developers.facebook.com/apps/1928081404776564/",
        return {
            "account_id": "act_368401904774563",
            "campaign_id": "120237328976970156",    # AAA test app campaign, Objective: OUTCOME_APP_PROMOTION
            "adset_name": "AAA Test Ad Set for OUTCOME_APP_PROMOTION",
            "optimization_goal": "APP_INSTALLS",    # this must be imcompatible with the campaign objective "OUTCOME_TRAFFIC"
            "billing_event": "IMPRESSIONS",
            "status": "PAUSED",
            "promoted_object": {
                "application_id": "1928081404776564",
                "object_store_url": "https://play.google.com/store/apps/details?id=com.taptap.global.lite",
            },
        }
    elif config_type == "use_adset_level_budgets":
        return {
            "account_id": "act_368401904774563",
            "campaign_id": "120237595006130156",
            "adset_name": "AAA Test Ad Set with Ad Set Level Budgets",
            "optimization_goal": "LINK_CLICKS",
            "billing_event": "IMPRESSIONS",
            "status": "PAUSED",
            "daily_budget": 1001,
            "bid_strategy": "LOWEST_COST_WITHOUT_CAP",
        }
    elif config_type == "1":
        return {
            "account_id": "act_368401904774563",
            "campaign_id": "120237595006130156",
            "adset_name": "AAA Test Ad Set with Ad Set Level Budgets",
            "optimization_goal": "LINK_CLICKS",
            "billing_event": "IMPRESSIONS",
            "status": "ACTIVE",
            "lifetime_budget": 100000,
            "bid_strategy": "COST_CAP", # if "COST_CAP", "billing_event" must be "IMPRESSIONS"
            "end_time": "2025-12-12T00:00:00-0000",
            "bid_amount": 100,
            "targeting": {
                "age_min": 18,
                "age_max": 65,
                "geo_locations": {"countries": ["US", "CN"]},
                "targeting_automation": {"advantage_audience": 1}
            }
        }
    elif config_type == "2":
        return {
        }


def test_create_adset(config_type: str = "use_adset_level_budgets"):
    print("=" * 60)
    print("Testing create ad set tool")
    print("=" * 60)
    res = create_adset_tool(**get_create_adset_config(config_type))
    print(json.dumps(res, indent=2, ensure_ascii=False))


def test_update_adset():
    print("=" * 60)
    print("Testing update ad set tool")
    print("=" * 60)
    res = asyncio.run(update_adset.ainvoke({
        "adset_id": "120237344008200156",    # AAA test ad set, Optimization goal: LINK_CLICKS
        "optimization_goal": "LINK_CLICKS",
        "daily_budget": 1000,
        "bid_strategy": "LOWEST_COST_WITHOUT_CAP",
        "frequency_control_specs": [
            {
                "event": "IMPRESSIONS",
                "interval_days": 7,
                "max_frequency": 3,
            }
        ],
    }))
    print(json.dumps(res, indent=2, ensure_ascii=False))


# test_get_adsets()
# test_create_adset(config_type="default")
# test_update_adset()
test_create_adset(config_type="2")
# test_update_adset()
# test_get_adset_details()
