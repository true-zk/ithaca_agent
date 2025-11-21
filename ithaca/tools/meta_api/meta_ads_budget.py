"""
Meta Ads Budget Tools.

- create_budget_schedule: create a budget schedule for a Meta Ads campaign
"""

from typing import Optional, Dict, Any, List
import json

from langchain.tools import tool

from ithaca.tools.meta_api.meta_ads_api import make_api_request, meta_api_tool
from ithaca.tools.meta_api.utils import APIToolErrors


# TODO: for now, set campaign level budget schedule only, 
# TODO: in the future we can set ad set level budget schedule.
@tool
@meta_api_tool
async def create_budget_schedule(
    campaign_id: str,
    budget_value: int,
    budget_value_type: str,
    time_start: int,
    time_end: int,
    access_token: Optional[str] = None
) -> str:
    """
    Create a budget schedule for a Meta Ads campaign.

    Allows scheduling budget increases based on anticipated high-demand periods.
    The times should be provided as Unix timestamps.
    
    Args:
        campaign_id: Meta Ads campaign ID.
        budget_value: Amount of budget increase. Interpreted based on budget_value_type.
        budget_value_type: Type of budget value - "ABSOLUTE" or "MULTIPLIER".
        time_start: Unix timestamp for when the high demand period should start.
        time_end: Unix timestamp for when the high demand period should end.
        access_token: Meta API access token (optional - will use cached token if not provided).
        
    Returns:
        A JSON string containing the ID of the created budget schedule or an error message.
    """
    if budget_value_type not in ["ABSOLUTE", "MULTIPLIER"]:
        return APIToolErrors.arg_invalid("budget_value_type", "str", budget_value_type, "Invalid budget_value_type. Must be ABSOLUTE or MULTIPLIER").to_json()

    endpoint = f"{campaign_id}/budget_schedules"

    params = {
        "budget_value": budget_value,
        "budget_value_type": budget_value_type,
        "time_start": time_start,
        "time_end": time_end,
    }

    try:
        data = await make_api_request(endpoint, access_token, params, method="POST")
        return json.dumps(data, indent=2)
    except Exception as e:
        return APIToolErrors.api_call_error(
            message="Failed to create budget schedule",
            details=str(e),
            params_sent=params,
        ).to_json()