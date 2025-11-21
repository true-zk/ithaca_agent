"""
Meta Ads ad Tools.
Cite from: https://developers.facebook.com/docs/marketing-api/reference/adgroup

- get_ads: Get ads for a Meta Ads by providing exactly one of "account_id", "campaign_id" or "adset_id".
- get_ad_details: Get details information about a specific Meta Ads ad.
- create_ad: Create a new ad with an existing creative.
- update_ad: Update an existing Meta Ads ad with new settings.
- delete_ad: Delete an existing Meta Ads ad.
"""
from typing import Optional, Dict, Any, List
import json

from langchain.tools import tool

from ithaca.tools.meta_api.meta_ads_api import make_api_request, meta_api_tool
from ithaca.tools.meta_api.utils import APIToolErrors
from ithaca.tools.meta_api.utils import STATUS_VALIDATOR


@tool
@meta_api_tool
async def get_ads(
    account_id: Optional[str] = None,
    campaign_id: Optional[str] = None,
    adset_id: Optional[str] = None,
    limit: int = 100,
    access_token: Optional[str] = None,
) -> str:
    """
    Get ads for a Meta Ads by providing exactly one of "account_id", "campaign_id" or "adset_id".
    The query fields are: "id,name,adset_id,campaign_id,status,creative,created_time,updated_time,bid_amount,conversion_domain,tracking_specs"

    Args:
        account_id: Meta Ads account ID (for example, "act_1234567890")
        campaign_id: Meta Ads campaign ID
        adset_id: Meta Ads adset ID
        limit: Maximum number of ads to return (default: 100)
        access_token: Meta API access token (optional - will use cached token if not provided)
    """
    if not account_id and not campaign_id and not adset_id:
        return APIToolErrors.error(
            message=" exactly one of account_id, campaign_id, or adset_id must be provided",
            example="get_ads(account_id='act_1234567890')"
        ).to_json()
    
    # order: adset -> campaign -> account
    if adset_id is not None:
        endpoint = f"{adset_id}/ads"
    elif campaign_id is not None:
        endpoint = f"{campaign_id}/ads"
    else:
        endpoint = f"{account_id}/ads"
    
    params = {
        "fields": "id,name,adset_id,campaign_id,status,creative,created_time,updated_time,bid_amount,conversion_domain,tracking_specs",
        "limit": limit
    }
    data = await make_api_request(endpoint, access_token, params)
    return json.dumps(data, indent=2)


@tool
@meta_api_tool
async def get_ad_details(
    ad_id: str,
    access_token: Optional[str] = None
) -> str:
    """
    Get details information about a specific Meta Ads ad.
    The query fields are: "id,name,adset_id,campaign_id,status,creative,created_time,updated_time,bid_amount,conversion_domain,tracking_specs,preview_shareable_link"
    
    Args:
        ad_id: Meta Ads ad ID
        access_token: Meta API access token (optional - will use cached token if not provided)
    """
    if not ad_id:
        return APIToolErrors.arg_missing("ad_id", "str", "Ad ID is required").to_json()
    
    endpoint = f"{ad_id}"
    params = {
        "fields": "id,name,adset_id,campaign_id,status,creative,created_time,updated_time,bid_amount,conversion_domain,tracking_specs,preview_shareable_link",
    }
    data = await make_api_request(endpoint, access_token, params)
    return json.dumps(data, indent=2)


@tool
@meta_api_tool
async def create_ad(
    account_id: str,
    adset_id: str,
    ad_name: str,
    creative_id: str,
    status: str = "PAUSED",
    bid_amount: Optional[int] = None,
    tracking_specs: Optional[List[Dict[str, Any]]] = None,
    access_token: Optional[str] = None
) -> str:
    """
    Create a new ad with an existing creative.

    Note:
        Dynamic Creative creatives require the parent ad set to have `is_dynamic_creative=true`.
        Otherwise, ad creation will fail with error_subcode 1885998.

    Args:
        account_id: Meta Ads account ID (for example, "act_1234567890")
        adset_id: Meta Ads adset ID where the ad will be placed
        ad_name: Ad name
        creative_id: Existing Meta Ads creative ID to be used for the ad
        status: Ad status (default: PAUSED)
        bid_amount: Bid amount in account currency (in cents for USD)
        tracking_specs: Optional tracking specifications (e.g., for pixel events).
                      Example: [{"action.type":"offsite_conversion","fb_pixel":["YOUR_PIXEL_ID"]}]
        access_token: Meta API access token (optional - will use cached token if not provided)
    """
    required_params = {
        "account_id": account_id,
        "adset_id": adset_id,
        "ad_name": ad_name,
        "creative_id": creative_id,
    }
    for key, value in required_params.items():
        if not value:
            return APIToolErrors.arg_missing(key, "str", f"{key} parameter cannot be empty").to_json()

    if not STATUS_VALIDATOR.validate(status):
        return STATUS_VALIDATOR.error(status).to_json()

    endpoint = f"{account_id}/ads"
    params = {
        "name": ad_name,
        "adset_id": adset_id,
        "creative": {"creative_id": creative_id},
        "status": status
    }
    
    # Add bid amount if provided
    if bid_amount is not None:
        params["bid_amount"] = str(bid_amount)
        
    # Add tracking specs if provided
    if tracking_specs is not None:
        params["tracking_specs"] = json.dumps(tracking_specs)
    
    try:
        data = await make_api_request(endpoint, access_token, params, method="POST")
        return json.dumps(data, indent=2)
    except Exception as e:
        error_msg = str(e)
        return APIToolErrors.api_call_error(
            message="Failed to create ad",
            details=error_msg,
            params_sent=params,
        ).to_json()


@tool
@meta_api_tool
async def update_ad(
    ad_id: str,
    status: Optional[str] = None,
    bid_amount: Optional[int] = None,
    tracking_specs: Optional[List[Dict[str, Any]]] = None,
    creative_id: Optional[str] = None,
    access_token: Optional[str] = None
) -> str:
    """
    Update an existing Meta Ads ad with new settings.
    
    Args:
        ad_id: Meta Ads ad ID
        status: Update ad status (ACTIVE, PAUSED, etc.)
        bid_amount: Bid amount in account currency (in cents for USD)
        tracking_specs: Optional tracking specifications (e.g., for pixel events).
        creative_id: ID of the creative to associate with this ad (changes the ad's image/content)
        access_token: Meta API access token (optional - will use cached token if not provided)
    """
    if not ad_id:
        return APIToolErrors.arg_missing("ad_id", "str", "Ad ID is required").to_json()

    endpoint = f"{ad_id}"
    params = {}
    if status:
        params["status"] = status
    if bid_amount is not None:
        params["bid_amount"] = str(bid_amount)
    if tracking_specs is not None: # Add tracking_specs to params if provided
        params["tracking_specs"] = json.dumps(tracking_specs)
    if creative_id is not None:
        params["creative"] = json.dumps({"creative_id": creative_id})

    if not params:
        return APIToolErrors.error("No update parameters provided (status, bid_amount, tracking_specs, or creative_id)").to_json()

    try:
        data = await make_api_request(endpoint, access_token, params, method="POST")
        return json.dumps(data, indent=2)
    except Exception as e:
        return APIToolErrors.api_call_error(
            message=f"Failed to update ad: {ad_id}",
            details=str(e),
            params_sent=params,
        ).to_json()


@tool
@meta_api_tool
async def delete_ad(
    ad_id: str,
    access_token: Optional[str] = None
) -> str:
    """
    Delete an existing Meta Ads ad.
    
    Args:
        ad_id: Meta Ads ad ID to delete
        access_token: Meta API access token (optional - will use cached token if not provided)
    """
    if not ad_id:
        return APIToolErrors.arg_missing("ad_id", "str", "Ad ID is required").to_json()
    endpoint = f"{ad_id}"
    try:
        data = await make_api_request(endpoint, access_token, None, method="DELETE")
        return json.dumps(data, indent=2)
    except Exception as e:
        return APIToolErrors.api_call_error(
            message=f"Failed to delete ad: {ad_id}",
            details=str(e),
            params_sent={},
        ).to_json()

