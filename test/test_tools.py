import sys
from pathlib import Path
import asyncio
import json

sys.path.insert(0, str(Path(__file__).parent.parent))

from ithaca.tools.webtools import fetch_pictures_from_web
from ithaca.tools.meta_api.meta_ads_adset import get_adsets, get_adset_details, create_adset
from ithaca.tools.meta_api.meta_ads_ad import get_ads, get_ad_details
from ithaca.tools.meta_api.meta_ads_insights import get_insights
from ithaca.tools.meta_api.meta_ads_creative import create_creative
from ithaca.tools.meta_api.meta_ads_ad_image import upload_ad_image
from ithaca.oauth.auth import auth_manager

if not auth_manager.get_access_token():
    auth_manager.authenticate(force_refresh=True)


def test_upload_ad_image():
    """Test upload ad image tool"""
    print("=" * 60)
    print("Testing upload ad image tool")
    print("=" * 60)
    res = asyncio.run(upload_ad_image.ainvoke({"account_id": "act_368401904774563", "image_url": "https://play-lh.googleusercontent.com/k8vYThDw5A8sAbAVHQ1yUmO9UWCwrKDf3ggTxa4Pve8rRFquhU0a5hCFqalGTEoVKQ=w240-h480-rw"}))
    print(res)


def test_create_creative():
    """Test create creative tool"""
    print("=" * 60)
    print("Testing create creative tool")
    print("=" * 60)
    res = asyncio.run(create_creative.ainvoke(
        {
            "account_id": "act_368401904774563", 
            "image_hash": "4bfcb0931415b1e8f9e2a4941f38cf12",
            "creative_name": "Test Creative",
            # "page_id": "120234963696360156",
            "link_url": "https://www.taptap.cn/",
            "message": "Test Message",
            "headline": "Test Headline",
            "description": "Test Description",
            "dynamic_creative_spec": None,
        }
    ))
    print(res)


# BUG: this tool is not working
def test_create_adset():
    """Test create ad set tool"""
    print("=" * 60)
    print("Testing create ad set tool")
    print("=" * 60)
    res = asyncio.run(create_adset.ainvoke(
        {"account_id": "act_368401904774563", 
        "campaign_id": "120237211377310156", 
        "adset_name": "Test Ad Set", 
        "optimization_goal": "LINK_CLICKS", 
        "billing_event": "LINK_CLICKS",
        "status": "PAUSED",
        "bid_amount": 100,
        # "daily_budget": 50,
        # "lifetime_budget": 1000,
        }))
    print(res)


def test_get_insights():
    """Test get insights tool"""
    print("=" * 60)
    print("Testing get insights tool")
    print("=" * 60)
    res = asyncio.run(get_insights.ainvoke({"id": "act_368401904774563", "level": "account"}))
    print(res)


def test_get_ads():
    """Test get ads tool"""
    print("=" * 60)
    print("Testing get ads tool")
    print("=" * 60)
    res = asyncio.run(get_ads.ainvoke({"account_id": "act_368401904774563"}))
    print(res)
    print("-" * 20)
    res = asyncio.run(get_ads.ainvoke({"adset_id": "23848616342330155"}))
    print(res)
    print("-" * 20)
    res = asyncio.run(get_ad_details.ainvoke({"ad_id": "23848616342380155"}))
    print(res)
    print("-" * 20)

def test_get_adsets():
    """Test get ad sets tool"""
    print("=" * 60)
    print("Testing get ad sets tool")
    print("=" * 60)
    res = asyncio.run(get_adsets.ainvoke({"account_id": "act_368401904774563"}))
    print(res)
    print("-" * 20)
    res = asyncio.run(get_adset_details.ainvoke({"adset_id": "23848616342330155"}))
    print(res)

def test_fetch_product_picture():
    """Test fetch product picture tool"""
    print("=" * 60)
    print("Testing fetch product picture tool")
    print("=" * 60)
    res = fetch_pictures_from_web.invoke({"url": "https://www.taptap.cn/"})
    print(res)


# test_get_ads()
# test_get_insights()
# test_get_adsets()
test_create_adset()
# test_create_creative()
# test_upload_ad_image()