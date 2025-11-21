"""
Meta Ads Campaign Tools.
A campaign is the highest level organizational structure within an ad account 
and should represent a single objective for an advertiser, 
for example, to drive page post engagement. 
Setting objective of the campaign will enforce validation on any ads added to the campaign 
to ensure they also have the correct objective.
Ctie from: https://developers.facebook.com/docs/marketing-api/reference/ad-campaign-group

- get_campaigns: Get campaigns for a Meta Ads account with optional filtering.
- get_campaign_details: Get details information about a specific Meta Ads campaign.
- create_campaign: Create a new Meta Ads campaign for the given Meta Ads account.
- update_campaign: Update an existing campaign in a Meta Ads account.
- delete_campaign: Delete an existing campaign in a Meta Ads account.
- unassociate_campaign: Unassociate a campaign from an ad account.
"""
from typing import Optional, Dict, Any, List
import json

from langchain.tools import tool

from ithaca.tools.meta_api.meta_ads_api import make_api_request, meta_api_tool
from ithaca.tools.meta_api.utils import valid_account_id, APIToolErrors
from ithaca.tools.meta_api.utils import (
    EFFECTIVE_STATUS_VALIDATOR, 
    STATUS_VALIDATOR, 
    OBJECTIVE_VALIDATOR, 
    BID_STRATEGY_VALIDATOR, 
    DELETE_STRATEGY_VALIDATOR,
)


@tool
@meta_api_tool
async def get_campaigns(
    account_id: str,
    effective_status: str = "",
    after: str = "",
    limit: int = 100,
    access_token: Optional[str] = None
):
    """
    Get campaigns for a Meta Ads account with optional effective_status filtering.
    The query fields are: "id,name,objective,status,daily_budget,lifetime_budget,buying_type,start_time,stop_time,created_time,updated_time,bid_strategy"
    
    Args:
        account_id: Meta Ads account ID (for example, "act_1234567890")
        effective_status: Filter campaigns by status (choose from "", "ACTIVE", "PAUSED", "ARCHIVED", "DELETED", "IN_PROCESS", "WITH_ISSUES"). 
            Default empty string "" means get all campaigns.
        after: Pagination cursor for next page
        limit: Maximum number of campaigns to return (default: 100)
        access_token: Meta API access token (optional - will use cached token if not provided)
    """
    if not account_id:
        return APIToolErrors.no_account_id().to_json()
    
    account_id = valid_account_id(account_id)

    endpoint = f"{account_id}/campaigns"
    params = {
        "fields": "id,name,objective,status,daily_budget,lifetime_budget,buying_type,start_time,stop_time,created_time,updated_time,bid_strategy",
        "limit": limit
    }

    if effective_status:
        if not EFFECTIVE_STATUS_VALIDATOR.validate(effective_status):
            return EFFECTIVE_STATUS_VALIDATOR.error(effective_status).to_json()
        params["effective_status"] = effective_status
    
    if after:
        params["after"] = after
    
    data = await make_api_request(endpoint, access_token, params)
    
    return json.dumps(data, indent=2)


@tool
@meta_api_tool
async def get_campaign_details(
    campaign_id: str,
    access_token: Optional[str] = None
):
    """
    Get details information about a specific Meta Ads campaign.
    The query fields are: "id,name,objective,status,daily_budget,lifetime_budget,buying_type,start_time,stop_time,created_time,updated_time,bid_strategy,special_ad_categories,special_ad_category_country,budget_remaining,configured_status"

    Args:
        campaign_id: Meta Ads campaign ID
        access_token: Meta API access token (optional - will use cached token if not provided)
    """
    if not campaign_id:
        return APIToolErrors.no_campaign_id().to_json()
    
    endpoint = f"{campaign_id}"
    params = {
        "fields": "id,name,objective,status,daily_budget,lifetime_budget,buying_type,start_time,stop_time,created_time,updated_time,bid_strategy,special_ad_categories,special_ad_category_country,budget_remaining,configured_status"
    }

    data = await make_api_request(endpoint, access_token, params)
    return json.dumps(data, indent=2)


# manipulate tools
@tool
@meta_api_tool
async def create_campaign(
    account_id: str,
    campaign_name: str,
    objective: str,
    status: str,
    special_ad_categories: Optional[List[str]] = None,
    daily_budget: Optional[int] = None,
    lifetime_budget: Optional[int] = None,
    buying_type: Optional[str] = None,
    bid_strategy: Optional[str] = None,
    bid_cap: Optional[int] = None,
    spend_cap: Optional[int] = None,
    campaign_budget_optimization: Optional[bool] = None,
    ab_test_control_setups: Optional[List[Dict[str, Any]]] = None,
    use_adset_level_budgets: bool = False,
    access_token: Optional[str] = None,
) -> str:
    """
    Create a new Meta Ads campaign for the given Meta Ads account.

    Args:
        account_id: Meta Ads account ID (for example, "act_1234567890")
        campaign_name: Campaign name
        objective: Campaign objective (ODAX, outcome-based). Must be one of:
                   OUTCOME_AWARENESS, OUTCOME_TRAFFIC, OUTCOME_ENGAGEMENT,
                   OUTCOME_LEADS, OUTCOME_SALES, OUTCOME_APP_PROMOTION.
                   Note: Legacy objectives like BRAND_AWARENESS, LINK_CLICKS,
                   CONVERSIONS, APP_INSTALLS, etc. are not valid for new
                   campaigns and will cause a 400 error. Use the outcome-based
                   values above (e.g., BRAND_AWARENESS → OUTCOME_AWARENESS).
        status: Initial campaign status (default: PAUSED)
        special_ad_categories: List of special ad categories if applicable
        daily_budget: Daily budget in account currency (in cents) as a string (only used if use_adset_level_budgets=False)
        lifetime_budget: Lifetime budget in account currency (in cents) as a string (only used if use_adset_level_budgets=False)
        buying_type: Buying type (e.g., 'AUCTION')
        bid_strategy: Bid strategy. Must be one of: 'LOWEST_COST_WITHOUT_CAP', 'LOWEST_COST_WITH_BID_CAP', 'COST_CAP', 'LOWEST_COST_WITH_MIN_ROAS'.
        bid_cap: Bid cap in account currency (in cents) as a string
        spend_cap: Spending limit for the campaign in account currency (in cents) as a string
        campaign_budget_optimization: Whether to enable campaign budget optimization (only used if use_adset_level_budgets=False)
        ab_test_control_setups: Settings for A/B testing (e.g., [{"name":"Creative A", "ad_format":"SINGLE_IMAGE"}])
        use_adset_level_budgets: If True, budgets will be set at the ad set level instead of campaign level (default: False)
        access_token: Meta API access token (optional - will use cached token if not provided)
    """
    if not account_id:
        return APIToolErrors.no_account_id().to_json()
    
    if not campaign_name:
        return APIToolErrors.arg_missing("campaign_name", "str", "Campaign name cannot be empty").to_json()

    if not objective:
        return APIToolErrors.arg_missing("objective", "str", "Campaign objective cannot be empty", "Use one of the following values: OUTCOME_AWARENESS, OUTCOME_TRAFFIC, OUTCOME_ENGAGEMENT, OUTCOME_LEADS, OUTCOME_SALES, OUTCOME_APP_PROMOTION").to_json()

    if not daily_budget and not lifetime_budget and not use_adset_level_budgets:
        return APIToolErrors.arg_missing(
            "daily_budget or lifetime_budget", 
            "int", 
            "Either daily_budget or lifetime_budget must be provided if use_adset_level_budgets is False"
            "daily_budget=1000 (10 USD) or lifetime_budget=10000 (100 USD)").to_json()
    
    if not OBJECTIVE_VALIDATOR.validate(objective):
        return OBJECTIVE_VALIDATOR.error(objective).to_json()

    if not STATUS_VALIDATOR.validate(status):
        return STATUS_VALIDATOR.error(status).to_json()

    if special_ad_categories is None:
        special_ad_categories = []
    
    endpoint = f"{account_id}/campaigns"
    params = {
        "name": campaign_name,
        "objective": objective,
        "status": status,
        "special_ad_categories": json.dumps(special_ad_categories),
    }

    # If agent does not set adset level budgets, sets campaign level budgets.
    if not use_adset_level_budgets:
        if daily_budget is not None:
            params["daily_budget"] = str(daily_budget)
        if lifetime_budget is not None:
            params["lifetime_budget"] = str(lifetime_budget)
        if campaign_budget_optimization is not None:
            params["campaign_budget_optimization"] = "true" if campaign_budget_optimization else "false"
    
    # Extra params
    if buying_type is not None:
        params["buying_type"] = buying_type
    if bid_strategy is not None:
        if not BID_STRATEGY_VALIDATOR.validate(bid_strategy):
            return BID_STRATEGY_VALIDATOR.error(bid_strategy).to_json()
        params["bid_strategy"] = bid_strategy
    if bid_cap is not None:
        params["bid_cap"] = str(bid_cap)
    if spend_cap is not None:
        params["spend_cap"] = str(spend_cap)
    if ab_test_control_setups is not None:
        params["ab_test_control_setups"] = json.dumps(ab_test_control_setups)
    
    try:
        data = await make_api_request(endpoint, access_token, params, method="POST")

        if use_adset_level_budgets:
            data["budget_strategy"] = "ad_set_level"
            data["note"] = "Campaign created with ad set level budgets. Set budgets when creating ad sets within this campaign."
        
        return json.dumps(data, indent=2)

    except Exception as e:
        return APIToolErrors.api_call_error(
            "Failed to create campaign",
            details=str(e),
            params_sent=params,
        ).to_json()


@tool
@meta_api_tool
async def update_campaign(
    campaign_id: str,
    campaign_name: Optional[str] = None,
    status: Optional[str] = None,
    special_ad_categories: Optional[List[str]] = None,
    daily_budget: Optional[int] = None,
    lifetime_budget: Optional[int] = None,
    bid_strategy: Optional[str] = None,
    bid_cap: Optional[int] = None,
    spend_cap: Optional[int] = None,
    campaign_budget_optimization: Optional[bool] = None,
    objective: Optional[str] = None,  # Add objective if it's updatable
    use_adset_level_budgets: Optional[bool] = None,
    access_token: Optional[str] = None,
) -> str:
    """
    Update an existing Meta Ads campaign.

    Args:
        campaign_id: Meta Ads campaign ID
        campaign_name: New campaign name
        status: New campaign status (choose from "ACTIVE", "PAUSED", "ARCHIVED", "DELETED", "IN_PROCESS", "WITH_ISSUES").
        special_ad_categories: List of special ad categories if applicable, Updating special_ad_categories might have specific API rules or might not be allowed after creation.
                                The API might require an empty list `[]` to clear categories. Check Meta Docs.
        daily_budget: New daily budget in account currency (in cents) as a string. 
                     Set to empty string "" to remove the daily budget.
        lifetime_budget: New lifetime budget in account currency (in cents) as a string.
                        Set to empty string "" to remove the lifetime budget.
        bid_strategy: New bid strategy (choose from "LOWEST_COST_WITHOUT_CAP", "LOWEST_COST_WITH_BID_CAP", "COST_CAP", "LOWEST_COST_WITH_MIN_ROAS").
        bid_cap: New bid cap in account currency (in cents) as a string
        spend_cap: New spending limit for the campaign in account currency (in cents) as a string
        campaign_budget_optimization: Enable/disable campaign budget optimization
        objective: New campaign objective (choose from "OUTCOME_AWARENESS", "OUTCOME_TRAFFIC", "OUTCOME_ENGAGEMENT", "OUTCOME_LEADS", "OUTCOME_SALES", "OUTCOME_APP_PROMOTION").
            Caution: Objective changes might reset learning or be restricted.
        use_adset_level_budgets: If True, removes campaign-level budgets to switch to ad set level budgets
        access_token: Meta API access token (optional - will use cached token if not provided)
    """
    if not campaign_id:
        return APIToolErrors.no_campaign_id().to_json()

    endpoint = f"{campaign_id}"
    params = {}
    
    # Add parameters to the request only if they are provided
    if campaign_name is not None:
        params["name"] = campaign_name
    if status is not None:
        if not STATUS_VALIDATOR.validate(status):
            return STATUS_VALIDATOR.error(status).to_json()
        params["status"] = status
    if special_ad_categories is not None:
        # Note: Updating special_ad_categories might have specific API rules or might not be allowed after creation.
        # The API might require an empty list `[]` to clear categories. Check Meta Docs.
        params["special_ad_categories"] = json.dumps(special_ad_categories)
    
    # Handle budget parameters based on use_adset_level_budgets setting
    if use_adset_level_budgets is not None:
        if use_adset_level_budgets:
            # Remove campaign-level budgets when switching to ad set level budgets
            params["daily_budget"] = ""
            params["lifetime_budget"] = ""
            if campaign_budget_optimization is not None:
                params["campaign_budget_optimization"] = "false"
        else:
            # If switching back to campaign-level budgets, use the provided budget values
            if daily_budget is not None:
                if daily_budget == "":
                    params["daily_budget"] = ""
                else:
                    params["daily_budget"] = str(daily_budget)
            if lifetime_budget is not None:
                if lifetime_budget == "":
                    params["lifetime_budget"] = ""
                else:
                    params["lifetime_budget"] = str(lifetime_budget)
            if campaign_budget_optimization is not None:
                params["campaign_budget_optimization"] = "true" if campaign_budget_optimization else "false"
    else:
        # Normal budget updates when not changing budget strategy
        if daily_budget is not None:
            # To remove budget, set to empty string
            if daily_budget == "":
                params["daily_budget"] = ""
            else:
                params["daily_budget"] = str(daily_budget)
        if lifetime_budget is not None:
            # To remove budget, set to empty string
            if lifetime_budget == "":
                params["lifetime_budget"] = ""
            else:
                params["lifetime_budget"] = str(lifetime_budget)
        if campaign_budget_optimization is not None:
            params["campaign_budget_optimization"] = "true" if campaign_budget_optimization else "false"
    
    if bid_strategy is not None:
        if not BID_STRATEGY_VALIDATOR.validate(bid_strategy):
            return BID_STRATEGY_VALIDATOR.error(bid_strategy).to_json()
        params["bid_strategy"] = bid_strategy
    if bid_cap is not None:
        params["bid_cap"] = str(bid_cap)
    if spend_cap is not None:
        params["spend_cap"] = str(spend_cap)
    if objective is not None:
        if not OBJECTIVE_VALIDATOR.validate(objective):
            return OBJECTIVE_VALIDATOR.error(objective).to_json()
        params["objective"] = objective # Caution: Objective changes might reset learning or be restricted

    if not params:
        return APIToolErrors.error("No update parameters provided").to_json()

    try:
        data = await make_api_request(endpoint, access_token, params, method="POST")
        
        # Add a note about budget strategy if switching to ad set level budgets
        if use_adset_level_budgets is not None and use_adset_level_budgets:
            data["budget_strategy"] = "ad_set_level"
            data["note"] = "Campaign updated to use ad set level budgets. Set budgets when creating ad sets within this campaign."
        
        return json.dumps(data, indent=2)

    except Exception as e:
        return APIToolErrors.api_call_error(
            f"Failed to update campaign: {campaign_id}",
            details=str(e),
            params_sent=params,
        ).to_json()


@tool
@meta_api_tool
async def delete_campaign(
    campaign_id: str,
    access_token: Optional[str] = None
) -> str:
    """
    Delete an existing Meta Ads campaign.

    Args:
        campaign_id: Meta Ads campaign ID
        access_token: Meta API access token (optional - will use cached token if not provided)
    """
    if not campaign_id:
        return APIToolErrors.no_campaign_id().to_json()
    endpoint = f"{campaign_id}"
    try:
        data = await make_api_request(endpoint, access_token, None, method="DELETE")
        return json.dumps(data, indent=2)
    except Exception as e:
        return APIToolErrors.api_call_error(
            message=f"Failed to delete campaign: {campaign_id}",
            details=str(e),
            params_sent={},
        ).to_json()


@tool
@meta_api_tool
async def unassociate_campaign(
    account_id: str,
    delete_strategy: str,
    before_date: Optional[str] = None,
    object_count: Optional[int] = None,
    access_token: Optional[str] = None
) -> str:
    """
    Unassociate a campaign from an ad account.
    
    Args:
        account_id: Meta Ads account ID (for example, "act_1234567890")
        delete_strategy: Delete strategy (choose from "DELETE_ANY", "DELETE_OLDEST", "DELETE_ARCHIVED_BEFORE")
        before_date: Date to unassociate campaigns before (YYYY-MM-DD)
        object_count: Number of objects to unassociate
        access_token: Meta API access token (optional - will use cached token if not provided)
    """
    if not account_id:
        return APIToolErrors.no_account_id().to_json()
    
    if not DELETE_STRATEGY_VALIDATOR.validate(delete_strategy):
        return DELETE_STRATEGY_VALIDATOR.error(delete_strategy).to_json()

    endpoint = f"{account_id}/campaigns"
    params = {
        "delete_strategy": delete_strategy,
    }
    if before_date is not None:
        params["before_date"] = before_date
    if object_count is not None:
        params["object_count"] = str(object_count)
    
    try:
        data = await make_api_request(endpoint, access_token, params, method="DELETE")
        return json.dumps({
            "message": f"Campaigns unassociated successfully from account: {account_id}",
            "details": data,
        }, indent=2)
    except Exception as e:
        return APIToolErrors.api_call_error(
            message=f"Failed to unassociate campaigns to account: {account_id} with error: {str(e)}",
            details=str(e),
            params_sent=params,
        ).to_json()
