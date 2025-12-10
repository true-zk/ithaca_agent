"""
Meta Ads Targeting Tools.

- search_interests: search for interests by query
- get_interests_suggestions: get suggestions for interests by list of interests
- search_behaviors: get all available behavior targeting options
- search_demographics: get demographic targeting options
- search_geo_locations: search for geographic targeting locations
- estimate_audience_size: estimate audience size for targeting specifications
"""
from typing import Optional, Dict, Any, List
import json

from ithaca.tools.meta_api.meta_ads_api import make_api_request, meta_api_tool
from ithaca.tools.meta_api.utils import APIToolErrors, valid_account_id, OPTIMIZATION_GOAL_VALIDATOR


@meta_api_tool
async def search_interests(
    query: str,
    limit: int = 20,
    access_token: Optional[str] = None,
) -> str:
    """
    Search for interests by query.
    
    Args:
        query: Query to search for interests (e.g., "sports", "travel", "food", etc.)
        limit: Maximum number of interests to return (default: 20)
        access_token: Meta API access token (optional - will use cached token if not provided)
    """
    if not query:
        return APIToolErrors.arg_missing("query", "str", "Query is required").to_json()
    
    endpoint = "search"
    params = {
        "type": "adinterest",
        "q": query,
        "limit": limit,
    }
    data = await make_api_request(endpoint, access_token, params)
    return json.dumps(data, indent=2)


@meta_api_tool
async def get_interests_suggestions(
    interest_list: List[str],
    limit: int = 20,
    access_token: Optional[str] = None,
) -> str:
    """
    Get suggestions for interests by list of interests.
    
    Args:
        interest_list: List of interests (e.g., ["sports", "travel", "food"])
        limit: Maximum number of interests to return (default: 20)
        access_token: Meta API access token (optional - will use cached token if not provided)
    """
    if not interest_list:
        return APIToolErrors.arg_missing("interest_list", "list", "Interest list is required").to_json()
    
    endpoint = "search"
    params = {
        "type": "adinterestsuggestion",
        "interest_list": json.dumps(interest_list),
        "limit": limit,
    }
    data = await make_api_request(endpoint, access_token, params)
    return json.dumps(data, indent=2)


@meta_api_tool
async def search_behaviors(
    limit: int = 50,
    access_token: Optional[str] = None,
) -> str:
    """
    Get all available behavior targeting options.
    
    Args:
        limit: Maximum number of results to return (default: 50)
        access_token: Meta API access token (optional - will use cached token if not provided)
    
    Returns:
        JSON string containing behavior targeting options with id, name, audience_size bounds, path, and description
    """
    endpoint = "search"
    params = {
        "type": "adTargetingCategory",
        "class": "behaviors",
        "limit": limit
    }
    
    data = await make_api_request(endpoint, access_token, params)
    
    return json.dumps(data, indent=2)


@meta_api_tool
async def search_demographics(
    demographic_class: str = "demographics",
    limit: int = 50,
    access_token: Optional[str] = None,
) -> str:
    """
    Get demographic targeting options.
    
    Args:
        demographic_class: Type of demographics to retrieve. Options: 'demographics', 'life_events', 
                          'industries', 'income', 'family_statuses', 'user_device', 'user_os' (default: 'demographics')
        limit: Maximum number of results to return (default: 50)
        access_token: Meta API access token (optional - will use cached token if not provided)
    
    Returns:
        JSON string containing demographic targeting options with id, name, audience_size bounds, path, and description
    """
    endpoint = "search"
    params = {
        "type": "adTargetingCategory",
        "class": demographic_class,
        "limit": limit
    }
    
    data = await make_api_request(endpoint, access_token, params)
    
    return json.dumps(data, indent=2)


@meta_api_tool
async def search_geo_locations(
    query: str,
    location_types: Optional[List[str]] = None,
    limit: int = 25,
    access_token: Optional[str] = None,
) -> str:
    """
    Search for geographic targeting locations.
    
    Args:
        query: Search term for locations (e.g., "New York", "California", "Japan")
        location_types: Types of locations to search. Options: ['country', 'region', 'city', 'zip', 
                       'geo_market', 'electoral_district']. If not specified, searches all types.
        limit: Maximum number of results to return (default: 25)
        access_token: Meta API access token (optional - will use cached token if not provided)

    Returns:
        JSON string containing location data with key, name, type, and geographic hierarchy information
    """
    if not query:
        return APIToolErrors.arg_missing("query", "str", "Query is required").to_json()
    
    endpoint = "search"
    params = {
        "type": "adgeolocation",
        "q": query,
        "limit": limit
    }
    
    if location_types:
        params["location_types"] = json.dumps(location_types)
    
    data = await make_api_request(endpoint, access_token, params)
    
    return json.dumps(data, indent=2)


# TODO: for now use 'reachestimate' api only, 
# TODO: in the future we can use 'delivery_estimate' api for more comprehensive estimation.
@meta_api_tool
async def estimate_audience_size(
    account_id: str,
    targeting: Dict[str, Any],
    # optimization_goal: str = "REACH",
    access_token: Optional[str] = None,
) -> str:
    """
    Estimate audience size for targeting specifications.
    This function provides comprehensive audience estimation for complex targeting combinations
    including demographics, geography, interests, and behaviors.
    
    Args:
        account_id: Meta Ads account ID (format: act_XXXXXXXXX)
        targeting: Complete targeting specification including demographics, geography, interests, etc.
                  Example: {
                      "age_min": 25,
                      "age_max": 65,
                      "geo_locations": {"countries": ["PL"]},
                      "flexible_spec": [
                          {"interests": [{"id": "6003371567474"}]},
                          {"interests": [{"id": "6003462346642"}]}
                      ]
                  }
        access_token: Meta API access token (optional - will use cached token if not provided)
    
    Returns:
        JSON string with audience estimation results including estimated_audience_size,
        reach_estimate, and targeting validation
    """
    if not account_id:
        return APIToolErrors.no_account_id().to_json()
    
    if not targeting:
        return APIToolErrors.arg_missing("targeting", "dict", "Targeting is required").to_json()
    
    # if not OPTIMIZATION_GOAL_VALIDATOR.validate(optimization_goal):
    #     return OPTIMIZATION_GOAL_VALIDATOR.error(optimization_goal).to_json()
    
    if not _has_geo_location(targeting) and not _has_custom_audience(targeting):
        return APIToolErrors.error(
            message="Targeting must have geo location or custom audience",
            details="Add geo_locations with countries/regions/cities/zips or include custom_audiences",
            example=json.dumps({
                    "geo_locations": {"countries": ["US"]},
                    "age_min": 25,
                    "age_max": 65
                }, indent=2)
        ).to_json()
    
    account_id = valid_account_id(account_id)
    
    endpoint = f"{account_id}/reachestimate"
    params = {
        "targeting_spec": targeting,
    }

    data = await make_api_request(endpoint, access_token, params)
    if "error" in data:
        try:
            err_wrapper = data.get("error", {})
            details_obj = err_wrapper.get("details", {})
            raw_err = details_obj.get("error", {}) if isinstance(details_obj, dict) else {}
            if (
                isinstance(raw_err, dict) and (
                    raw_err.get("error_subcode") == 1885364 or
                    raw_err.get("error_user_title") == "Missing Target Audience Location"
                )
            ):
                return json.dumps({
                    "error": "Missing target audience location",
                    "details": raw_err.get("error_user_msg") or "Select at least one location, or choose a custom audience.",
                    "endpoint_used": f"{account_id}/reachestimate",
                    "action_required": "Add geo_locations with at least one of countries/regions/cities/zips or include custom_audiences.",
                    "blame_field_specs": raw_err.get("error_data", {}).get("blame_field_specs") if isinstance(raw_err.get("error_data"), dict) else None
                }, indent=2)
        except Exception as e:
            return APIToolErrors.api_call_error(
                message="Error estimating audience size",
                details=str(e),
                params_sent=params
            ).to_json()
    elif "data" in data:
        data = data["data"]
        if isinstance(data, list) and len(data) > 0:
            return json.dumps(
                {
                    "success": True,
                    "account_id": account_id,
                    "targeting": targeting,
                    # "optimization_goal": optimization_goal,
                    "estimated_audience_size": data[0].get("estimate_mau", 0),
                    "estimate_details": {
                        "monthly_active_users": data[0].get("estimate_mau", 0),
                        "daily_outcomes_curve": data[0].get("estimate_dau", []),
                        "bid_estimate": data[0].get("bid_estimates", {}),
                        "unsupported_targeting": data[0].get("unsupported_targeting", [])
                    },
                    "raw_response": data
                }, indent=2
            )
        elif isinstance(data, list) and len(data) == 0:
            return APIToolErrors.api_call_error(
                message="No estimation data returned",
                details=json.dumps(data, indent=2),
                params_sent=params
            ).to_json()
        elif isinstance(data, dict):
            lb = data.get("users_lower_bound", data.get("estimate_mau_lower_bound"))
            ub = data.get("users_upper_bound", data.get("estimate_mau_upper_bound"))
            estimate_ready = data.get("estimate_ready")
            midpoint = None
            try:
                if isinstance(lb, (int, float)) and isinstance(ub, (int, float)):
                    midpoint = int((lb + ub) / 2)
            except Exception:
                midpoint = None
            
            return json.dumps(
                {
                    "success": True,
                    "account_id": account_id,
                    "targeting": targeting,
                    # "optimization_goal": optimization_goal,
                    "estimated_audience_size": midpoint if midpoint is not None else 0,
                    "estimate_details": {
                        "users_lower_bound": lb,
                        "users_upper_bound": ub,
                        "estimate_ready": estimate_ready
                    },
                    "raw_response": data
                }, indent=2
            )
        else:
            return APIToolErrors.api_call_error(
                message="Unexpected response format",
                details=json.dumps(data, indent=2),
                params_sent=params
            ).to_json()


# Helper functions
def _has_geo_location(targeting: Dict[str, Any]) -> bool:
    """Check if targeting has geo location."""
    geo = targeting.get("geo_locations", {})
    if isinstance(geo, dict):
        for key in ["countries","regions","cities","zips","geo_markets","country_groups"]:
            if key in geo and geo[key] is not None and isinstance(geo[key], list) and len(geo[key]) > 0:
                return True
    return False


def _has_custom_audience(targeting: Dict[str, Any]) -> bool:
    """Check if targeting has custom audience."""
    custom_audiences = targeting.get("custom_audiences", [])
    if isinstance(custom_audiences, list) and len(custom_audiences) > 0:
        return True
    flexible_spec = targeting.get("flexible_spec", [])
    if isinstance(flexible_spec, list):
        for spec in flexible_spec:
            if isinstance(spec, dict):
                spec_audiences = spec.get("custom_audiences", [])
                if isinstance(spec_audiences, list) and len(spec_audiences) > 0:
                    return True
    return False