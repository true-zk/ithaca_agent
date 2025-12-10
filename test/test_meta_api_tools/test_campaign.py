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
    # expires_at = auth_manager.token.created_at + auth_manager.token.expires_in
    # print(f"Expires in: {expires_at - int(time.time())} seconds")


# Test tools
from ithaca.tools.meta_api.meta_ads_campaign import (
    get_campaigns, 
    get_campaign_details, 
    create_campaign,
    update_campaign,
    delete_campaign,
    unassociate_campaign,
)


def test_get_campaigns():
    """Test get campaigns tool"""
    print("=" * 60)
    print("Testing get campaigns tool")
    print("=" * 60)
    res = asyncio.run(get_campaigns.ainvoke({"account_id": "act_368401904774563"}))
    print(json.dumps(res, indent=2))


def test_get_campaign_details(campaign_id: str):
    """Test get campaign details tool"""
    print("=" * 60)
    print("Testing get campaign details tool")
    print("=" * 60)
    res = asyncio.run(get_campaign_details.ainvoke({"campaign_id": campaign_id}))
    print(json.dumps(res, indent=2))


def get_create_campaign_config(config_type: str = "default"):
    """Get create campaign config"""
    if config_type == "default":
        return {
            "account_id": "act_368401904774563", 
            "campaign_name": "AAA Test Campaign", 
            "objective": "OUTCOME_TRAFFIC", 
            "status": "PAUSED",
            "daily_budget": 1000,
            # "lifetime_budget": 10000,
            "buying_type": "AUCTION",
            "bid_strategy": "LOWEST_COST_WITHOUT_CAP",
            "campaign_budget_optimization": True,
        }
    elif config_type == "app":
        return {
            "account_id": "act_368401904774563", 
            "campaign_name": "AAA Test APP Campaign", 
            "objective": "OUTCOME_APP_PROMOTION", 
            "status": "PAUSED",
            "daily_budget": 1000,
            # "lifetime_budget": 10000,
            "buying_type": "AUCTION",
            "bid_strategy": "LOWEST_COST_WITHOUT_CAP",
            "campaign_budget_optimization": True,
        }
    elif config_type == "use_adset_level_budgets":
        return {
            "account_id": "act_368401904774563", 
            "campaign_name": "AAA Test Campaign with Ad Set Level Budgets", 
            "objective": "OUTCOME_TRAFFIC", 
            "status": "PAUSED",
            "buying_type": "AUCTION",
            "use_adset_level_budgets": True,
        }


def test_create_campaign(config_type: str = "default"):
    """Test create campaign tool"""
    print("=" * 60)
    print("Testing create campaign tool")
    print("=" * 60)
    res = asyncio.run(create_campaign.ainvoke(get_create_campaign_config(config_type)))
    print(json.dumps(res, indent=2, ensure_ascii=False))


from ithaca.tools.meta_api.meta_ads_campaign import create_campaign_tool
def test_create_campaign_new():
    """Test create campaign tool with new config"""
    print("=" * 60)
    print("Testing create campaign tool with new config")
    print("=" * 60)
    res = create_campaign_tool(
        account_id="act_368401904774563",
        campaign_name="BBB Test Campaign",
        objective="OUTCOME_TRAFFIC",
        # status="PAUSED",
        # bid_strategy="LOWEST_COST_WITHOUT_CAP",
    )
    print(json.dumps(res, indent=2, ensure_ascii=False))


# test_get_campaigns()
test_get_campaign_details(campaign_id="120237595006130156")
# test_create_campaign(config_type="app")
# test_create_campaign(config_type="use_adset_level_budgets")
# test_create_campaign_new()