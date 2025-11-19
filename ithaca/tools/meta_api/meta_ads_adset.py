"""
Meta Ads adset Tools.
An ad set is a group of ads that share the same daily or lifetime budget, 
schedule, bid type, bid info, and targeting data. 
Ad sets enable you to group ads according to your criteria, 
and you can retrieve the ad-related statistics that apply to a set.
Ctie from: https://developers.facebook.com/docs/marketing-api/reference/ad-campaign

- get_adsets: Get ad sets for a Meta Ads account with optional filtering by campaign.
- get_adset_details: Get details information about a specific Meta Ads ad set.
- create_adset: Create a new ad set in a Meta Ads account.
- update_adset: Update an existing Meta Ads ad set with new settings inluding frequency_control_specs and budgets.
- delete_adset: Delete an existing Meta Ads ad set.
"""
from typing import Optional, Dict, Any, List
import json

from langchain.tools import tool

from ithaca.tools.meta_api.meta_ads_api import make_api_request, meta_api_tool
from ithaca.tools.meta_api.utils import valid_account_id, APIToolErrors
from ithaca.tools.meta_api.utils import enum_arg_validators


@tool
@meta_api_tool
async def get_adsets(
    account_id: str,
    campaign_id: str = "",
    limit: int = 10,
    access_token: Optional[str] = None,
) -> str:
    """
    Get ad sets for a Meta Ads account with optional filtering by campaign.
    The query fields are: "id,name,campaign_id,status,daily_budget,lifetime_budget,targeting,bid_amount,bid_strategy,optimization_goal,billing_event,start_time,end_time,created_time,updated_time,is_dynamic_creative,frequency_control_specs{event,interval_days,max_frequency}"
    
    Args:
        account_id: Meta Ads account ID (for example, "act_1234567890")
        campaign_id: Optional campaign ID to filter ad sets by. (default: "")
            Default empty string "" means get all ad sets.
        limit: Maximum number of ad sets to return (default: 10)
        access_token: Meta API access token (optional - will use cached token if not provided)
    """
    if not account_id:
        return APIToolErrors.no_account_id().to_json()
    
    endpoint = f"{valid_account_id(account_id)}/adsets" if not campaign_id else f"{campaign_id}/adsets"
    params = {
        "fields": "id,name,campaign_id,status,daily_budget,lifetime_budget,targeting,bid_amount,bid_strategy,optimization_goal,billing_event,start_time,end_time,created_time,updated_time,is_dynamic_creative,frequency_control_specs{event,interval_days,max_frequency}",
        "limit": limit
    }
    
    data = await make_api_request(endpoint, access_token, params)
    return json.dumps(data, indent=2)


@tool
@meta_api_tool
async def get_adset_details(
    adset_id: str,
    access_token: Optional[str] = None,
) -> str:
    """
    Get details information about a specific Meta Ads ad set.
    The query fields are: "id,name,campaign_id,status,frequency_control_specs{event,interval_days,max_frequency},daily_budget,lifetime_budget,targeting,bid_amount,bid_strategy,optimization_goal,billing_event,start_time,end_time,created_time,updated_time,attribution_spec,destination_type,promoted_object,pacing_type,budget_remaining,dsa_beneficiary,is_dynamic_creative"
    
    Args:
        adset_id: Meta Ads ad set ID
        access_token: Meta API access token (optional - will use cached token if not provided)
    """
    if not adset_id:
        return APIToolErrors.arg_missing("adset_id", "str", "Ad set ID is required").to_json()
    
    endpoint = f"{adset_id}"
    params = {
        "fields": "id,name,campaign_id,status,frequency_control_specs{event,interval_days,max_frequency},daily_budget,lifetime_budget,targeting,bid_amount,bid_strategy,optimization_goal,billing_event,start_time,end_time,created_time,updated_time,attribution_spec,destination_type,promoted_object,pacing_type,budget_remaining,dsa_beneficiary,is_dynamic_creative",
    }
    data = await make_api_request(endpoint, access_token, params)
    return json.dumps(data, indent=2)


@tool
@meta_api_tool
async def create_adset(
    account_id: str, 
    campaign_id: str, 
    adset_name: str,
    optimization_goal: str,
    billing_event: str,
    status: str = "PAUSED",
    daily_budget: Optional[int] = None,
    lifetime_budget: Optional[int] = None,
    targeting: Optional[Dict[str, Any]] = None, # TODO: targeting param is abtrary dict, we need to abstract and validate it.
    bid_amount: Optional[int] = None,
    bid_strategy: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    dsa_beneficiary: Optional[str] = None,
    promoted_object: Optional[Dict[str, Any]] = None,
    destination_type: Optional[str] = None,
    is_dynamic_creative: Optional[bool] = None,
    access_token: Optional[str] = None
) -> str:
    """
    Create a new ad set in a Meta Ads account.
    
    Args:
        account_id: Meta Ads account ID (for example, "act_1234567890")
        campaign_id: Meta Ads campaign ID this ad set belongs to
        adset_name: Ad set name
        optimization_goal: Conversion optimization goal (e.g., 'LINK_CLICKS', 'REACH', 'CONVERSIONS', 'APP_INSTALLS')
        billing_event: How you're charged (e.g., 'IMPRESSIONS', 'LINK_CLICKS')
        status: Initial ad set status (default: PAUSED)
        daily_budget: Daily budget in account currency (in cents) as a string
        lifetime_budget: Lifetime budget in account currency (in cents) as a string
        targeting: Targeting specifications including age, location, interests, etc.
                  Use targeting_automation.advantage_audience=1 for automatic audience finding
        bid_amount: Bid amount in account currency (in cents)
        bid_strategy: Bid strategy (e.g., 'LOWEST_COST', 'LOWEST_COST_WITH_BID_CAP')
        start_time: Start time in ISO 8601 format (e.g., '2023-12-01T12:00:00-0800')
        end_time: End time in ISO 8601 format
        dsa_beneficiary: DSA beneficiary (person/organization benefiting from ads) for European compliance
        promoted_object: Mobile app configuration for APP_INSTALLS campaigns. Required fields: application_id, object_store_url.
                        Optional fields: custom_event_type, pixel_id, page_id.
                        Example: {"application_id": "123456789012345", "object_store_url": "https://apps.apple.com/app/id123456789"}
        destination_type: Where users are directed after clicking the ad (e.g., 'APP_STORE', 'DEEPLINK', 'APP_INSTALL', 'ON_AD').
                          Required for mobile app campaigns and lead generation campaigns.
                          Use 'ON_AD' for lead generation campaigns where user interaction happens within the ad.
        is_dynamic_creative: Enable Dynamic Creative for this ad set (required when using dynamic creatives with asset_feed_spec/dynamic_creative_spec).
        access_token: Meta API access token (optional - will use cached token if not provided)
    """
    # Check required parameters
    
    if not account_id:
        return APIToolErrors.no_account_id().to_json()
    
    required_params = {
        "campaign_id": campaign_id,
        "adset_name": adset_name,
        "optimization_goal": optimization_goal,
        "billing_event": billing_event,
    }
    
    for key, value in required_params.items():
        if not value:
            return APIToolErrors.arg_missing(key, "str", f"{key} parameter cannot be empty").to_json()
    
    enum_params = {
        "optimization_goal": optimization_goal,
        "billing_event": billing_event,
        "status": status,
        "bid_strategy": bid_strategy,
        "destination_type": destination_type,
    }

    for key, value in enum_params.items():
        if value and not enum_arg_validators[key].validate(value):
            return enum_arg_validators[key].error(value).to_json()
    
    # Validate mobile app parameters for APP_INSTALLS campaigns
    if optimization_goal == "APP_INSTALLS":
        if not promoted_object:
            return APIToolErrors.arg_missing(
                "promoted_object",
                "dict",
                "promoted_object is required for APP_INSTALLS optimization goal, and 'application_id', 'object_store_url' are required fields",
            ).to_json()
        
        # required fields validation
        if "application_id" not in promoted_object or "object_store_url" not in promoted_object:
            return APIToolErrors.arg_invalid(
                "promoted_object",
                "dict",
                promoted_object,
                "promoted_object must be a dictionary with at least 'application_id' and 'object_store_url' fields",
            ).to_json()
        
        # Validate store URL format
        store_url = promoted_object["object_store_url"]
        valid_store_patterns = [
            "apps.apple.com",  # iOS App Store
            "play.google.com",  # Google Play Store
            "itunes.apple.com"  # Alternative iOS format
        ]
        if not any(pattern in store_url for pattern in valid_store_patterns):
            return APIToolErrors.arg_invalid(
                "promoted_object",
                "dict",
                promoted_object,
                "object_store_url in promoted_object must be from App Store (apps.apple.com) or Google Play (play.google.com)",
            ).to_json()
    
    # BUG: meta_ads_mcp use this validator, but it does not match the API doc
    # ref: https://developers.facebook.com/docs/marketing-api/reference/ad-account/adsets/v24.0
    # ref: https://developers.facebook.com/docs/marketing-api/reference/ad-campaign
    # if destination_type:
    #     valid_destination_types = ["APP_STORE", "DEEPLINK", "APP_INSTALL", "ON_AD"]
    #     if destination_type not in valid_destination_types:
    #         return json.dumps({
    #             "error": f"Invalid destination_type: {destination_type}",
    #             "valid_values": valid_destination_types
    #         }, indent=2)
    
    # Basic targeting is required if not provided
    if not targeting:
        targeting = {
            "age_min": 18,
            "age_max": 65,
            "geo_locations": {"countries": ["US"]},
            "targeting_automation": {"advantage_audience": 1}
        }
    
    endpoint = f"{account_id}/adsets"
    params = {
        "name": adset_name,
        "campaign_id": campaign_id,
        "status": status,
        "optimization_goal": optimization_goal,
        "billing_event": billing_event,
        "targeting": json.dumps(targeting)  # Properly format as JSON string
    }
    
    # Convert budget values to strings if they aren't already
    if daily_budget is not None:
        params["daily_budget"] = str(daily_budget)
    
    if lifetime_budget is not None:
        params["lifetime_budget"] = str(lifetime_budget)
    
    # Add other parameters if provided
    if bid_amount is not None:
        params["bid_amount"] = str(bid_amount)
    
    if bid_strategy:
        params["bid_strategy"] = bid_strategy
    
    if start_time:
        params["start_time"] = start_time
    
    if end_time:
        params["end_time"] = end_time
    
    # Add DSA beneficiary if provided
    if dsa_beneficiary:
        params["dsa_beneficiary"] = dsa_beneficiary
    
    # Add mobile app parameters if provided
    if promoted_object:
        params["promoted_object"] = json.dumps(promoted_object)
    
    if destination_type:
        params["destination_type"] = destination_type
    
    # Enable Dynamic Creative if requested
    if is_dynamic_creative is not None:
        params["is_dynamic_creative"] = "true" if bool(is_dynamic_creative) else "false"
    
    try:
        data = await make_api_request(endpoint, access_token, params, method="POST")
        return json.dumps(data, indent=2)
    except Exception as e:
        error_msg = str(e)
        
        # Enhanced error handling for DSA beneficiary issues
        if "permission" in error_msg.lower() or "insufficient" in error_msg.lower():
            return APIToolErrors.error(
                message="Insufficient permissions to set DSA beneficiary. Please ensure you have business_management permissions.",
                details=error_msg,
                params_sent=params,
                extra_fields={"permission_required": True}
            ).to_json()
        elif "dsa_beneficiary" in error_msg.lower() and ("not supported" in error_msg.lower() or "parameter" in error_msg.lower()):
            return APIToolErrors.error(
                message="DSA beneficiary parameter not supported in this API version. Please set DSA beneficiary manually in Facebook Ads Manager.",
                details=error_msg,
                params_sent=params,
                extra_fields={"manual_setup_required": True}
            ).to_json()
        elif "benefits from ads" in error_msg or "DSA beneficiary" in error_msg:
            return APIToolErrors.error(
                message="DSA beneficiary required for European compliance. Please provide the person or organization that benefits from ads in this ad set.",
                details=error_msg,
                params_sent=params,
                extra_fields={"dsa_required": True}
            ).to_json()
        else:
            return APIToolErrors.api_call_error(
                message="Failed to create ad set",
                details=error_msg,
                params_sent=params,
            ).to_json()


@tool
@meta_api_tool
async def update_adset(
    adset_id: str,
    frequency_control_specs: Optional[List[Dict[str, Any]]] = None,
    bid_strategy: Optional[str] = None,
    bid_amount: Optional[int] = None,
    status: Optional[str] = None,
    targeting: Optional[Dict[str, Any]] = None,
    optimization_goal: Optional[str] = None,
    daily_budget: Optional[int] = None,
    lifetime_budget: Optional[int] = None,
    access_token: Optional[str] = None
) -> str:
    """
    Update an existing Meta Ads ad set with new settings inluding frequency_control_specs and budgets.

    Args:
        adset_id: Meta Ads ad set ID
        frequency_control_specs: List of frequency control specifications 
                                 (e.g. [{"event": "IMPRESSIONS", "interval_days": 7, "max_frequency": 3}])
        bid_strategy: Bid strategy (e.g., 'LOWEST_COST_WITH_BID_CAP')
        bid_amount: Bid amount in account currency (in cents for USD)
        status: Update ad set status (ACTIVE, PAUSED, etc.)
        targeting: Complete targeting specifications (will replace existing targeting)
                  (e.g. {"targeting_automation":{"advantage_audience":1}, "geo_locations": {"countries": ["US"]}})
        optimization_goal: Conversion optimization goal (e.g., 'LINK_CLICKS', 'CONVERSIONS', 'APP_INSTALLS', etc.)
        daily_budget: Daily budget in account currency (in cents) as a string
        lifetime_budget: Lifetime budget in account currency (in cents) as a string
        is_dynamic_creative: Enable/disable Dynamic Creative for this ad set.
        access_token: Meta API access token (optional - will use cached token if not provided)
    """
    if not adset_id:
        return APIToolErrors.arg_missing("adset_id", "str", "Ad set ID is required").to_json()
    
    enum_params = {
        "bid_strategy": bid_strategy,
        "status": status,
        "optimization_goal": optimization_goal,
    }

    for key, value in enum_params.items():
        if value and not enum_arg_validators[key].validate(value):
            return enum_arg_validators[key].error(value).to_json()

    endpoint = f"{adset_id}"
    params = {}

    if frequency_control_specs is not None:
        params["frequency_control_specs"] = json.dumps(frequency_control_specs)
    
    if bid_strategy is not None:
        params["bid_strategy"] = bid_strategy
    
    if bid_amount is not None:
        params["bid_amount"] = str(bid_amount)
    
    if status is not None:
        params["status"] = status
    
    if targeting is not None:
        params["targeting"] = json.dumps(targeting)
    
    if optimization_goal:
        params["optimization_goal"] = optimization_goal
    
    if daily_budget is not None:
        params["daily_budget"] = str(daily_budget)
    
    if lifetime_budget is not None:
        params["lifetime_budget"] = str(lifetime_budget)
    
    try:
        data = await make_api_request(endpoint, access_token, params, method="POST")
        return json.dumps(data, indent=2)
    except Exception as e:
        return APIToolErrors.api_call_error(
            message=f"Failed to update ad set: {adset_id}",
            details=str(e),
            params_sent=params,
        ).to_json()


@tool
@meta_api_tool
async def delete_adset(
    adset_id: str,
    access_token: Optional[str] = None
) -> str:
    """
    Delete an existing Meta Ads ad set.

    Args:
        adset_id: Meta Ads ad set ID
        access_token: Meta API access token (optional - will use cached token if not provided)
    """
    if not adset_id:
        return APIToolErrors.arg_missing("adset_id", "str", "Ad set ID is required").to_json()
    endpoint = f"{adset_id}"
    try:
        data = await make_api_request(endpoint, access_token, None, method="DELETE")
        return json.dumps({
            "message": "Ad set deleted successfully",
            "adset_id": adset_id,
        }, indent=2)
    except Exception as e:
        return APIToolErrors.api_call_error(
            message=f"Failed to delete ad set: {adset_id}",
            details=str(e),
            params_sent={},
        ).to_json()