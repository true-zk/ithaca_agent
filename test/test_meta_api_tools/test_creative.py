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
from ithaca.tools.meta_api.meta_ads_creative import (
    get_creative_by_account,
    get_creatives_by_ad,
    get_creative_details,
    create_creative_tool,
    update_creative,
    delete_creative,
)
from ithaca.tools.meta_api.meta_ads_ad_image import upload_ad_image


def test_get_creative_by_account():
    print("=" * 60)
    print("Testing get creative by account tool")
    print("=" * 60)
    res = asyncio.run(get_creative_by_account.ainvoke({
        "account_id": "act_368401904774563",
    }))
    print(json.dumps(res, indent=2, ensure_ascii=False))


def test_get_creatives_by_ad():
    print("=" * 60)
    print("Testing get creatives by ad tool")
    print("=" * 60)
    res = asyncio.run(get_creatives_by_ad.ainvoke({
        "ad_id": "23848616342380155",
    }))
    print(json.dumps(res, indent=2, ensure_ascii=False))


def test_get_creative_details(id):
    print("=" * 60)
    print("Testing get creative details tool")
    print("=" * 60)
    res = asyncio.run(get_creative_details.ainvoke({
        "creative_id": "1626572912117510" if not id else id,
    }))
    print(json.dumps(res, indent=2, ensure_ascii=False))


def get_test_creative_image_config(config: str = "default"):
    if config == "default":
        return {
            "image_url": "https://cdn.pixabay.com/photo/2025/11/28/15/29/zebras-9983175_1280.jpg",
            
            "account_id": "act_368401904774563",
            "image_hash": None,
            "page_id": "101519255589335",
            "creative_name": "Test Creative AAAA",
            "message": "Test Message AAAA",
            "headline": "Test Headline AAAA",
            "description": "Test Description AAAA",
        }
    elif config == "dynamic":
        return {
            "image_url": "https://cdn.pixabay.com/photo/2025/10/25/19/34/heart-9916675_1280.jpg",
            
            "account_id": "act_368401904774563",
            "image_hash": None,
            "page_id": "101519255589335",
            "creative_name": "Test Creative dynamic with open link",
            "message": "Test Message dynamic",
            "headlines": ["Test Headline AAAA", "Test Headline BBBB"],
            "descriptions": ["Test Description AAAA", "Test Description BBBB"],
            "call_to_action_type": "OPEN_LINK",
        }


def test_create_creative(config: str = "default"):
    print("=" * 60)
    print("Testing create creative tool")
    print("=" * 60)

    config_ = get_test_creative_image_config(config)
    
    print("Uploading test image...")
    res = asyncio.run(upload_ad_image.ainvoke({
        "account_id": "act_368401904774563",
        "image_url": config_["image_url"],
    }))
    
    print(json.dumps(res, indent=2, ensure_ascii=False))
    image_hash = res["image_hash"]
    config_.update({"image_hash": image_hash})
    config_.pop("image_url")

    res = create_creative_tool(**config_)
    print(json.dumps(res, indent=2, ensure_ascii=False))


def test_create_creative_with_multiple_images(config: str = "dynamic"):
    print("=" * 60)
    print("Testing create creative with multiple images tool")
    print("=" * 60)
    config_ = get_test_creative_image_config(config)
    config_.pop("image_url")
    config_["image_hash"] = [
        "39e90fa093c5cdb1f9adf8bdb2784f38",
        "f2679fe83200920fca39859ea356b3c3",
    ]
    config_["creative_name"] = "Test Creative dynamic with multiple images"
    res = create_creative_tool(**config_)
    print(json.dumps(res, indent=2, ensure_ascii=False))


#BUG: Update creative is not working.
def test_update_creative():
    print("=" * 60)
    print("Testing update creative tool")
    print("=" * 60)
    config_ = {
        "creative_id": "2000975177363248",
        "status": "ACTIVE",
        "call_to_action_type": "OPEN_LINK"
    }

    res = asyncio.run(update_creative.ainvoke(config_))
    print(json.dumps(res, indent=2, ensure_ascii=False))


# test_get_creative_by_account()
# test_get_creatives_by_ad()
# test_get_creative_details("882403964227280")    # creative may in process status after creation
# test_create_creative("default")
# test_create_creative("dynamic")
test_create_creative_with_multiple_images()
# test_get_creative_details("2000975177363248")
# test_update_creative()