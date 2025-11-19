"""
Meta Ads Account Tools.

- get_ad_accounts: Get Meta Ads accounts accessible by a user.
- get_ad_account_info: Get detailed information about a specific Meta Ads account.
"""
from typing import Optional, List, Dict, Any
import json

from langchain.tools import tool

from ithaca.tools.meta_api.meta_ads_api import make_api_request, meta_api_tool
from ithaca.tools.meta_api.utils import valid_account_id, APIToolErrors


async def _get_accounts_api_call(user_id: str, limit: int, access_token: Optional[str] = None) -> Dict[str, Any]:
    endpoint = f"{user_id}/adaccounts"
    params = {
        "fields": "id,name,account_id,account_status,amount_spent,balance,currency,age,business_city,business_country_code",
        "limit": limit
    }
    data = await make_api_request(endpoint, access_token, params)
    return data

@tool
@meta_api_tool
async def get_ad_accounts(user_id: str = "me", limit: int = 100, access_token: Optional[str] = None) -> str:
    """
    Get Meta Ads accounts accessible by a user.
    
    Args:
        user_id: Meta user ID or "me" for the current user
        limit: Maximum number of accounts to return (default: 200)
        access_token: Meta API access token (optional - will use cached token if not provided)
    """
    data = await _get_accounts_api_call(user_id, limit, access_token)
    return json.dumps(data, indent=2)


@tool
@meta_api_tool
async def get_ad_account_info(account_id: str,access_token: Optional[str] = None) -> str:
    """
    Get detailed information about a specific Meta Ads account.

    Args:
        account_id: Meta Ads account ID (for example, "act_1234567890")
        access_token: Meta API access token (optional - will use cached token if not provided)
    """
    if not account_id:
        return APIToolErrors.no_account_id().to_json()
    
    account_id = valid_account_id(account_id)

    endpoint = f"{account_id}"
    params = {
        "fields": "id,name,account_id,account_status,amount_spent,balance,currency,age,business_city,business_country_code,timezone_name"
    }

    data = await make_api_request(endpoint, access_token, params)

    # Handle accessible errors
    if "error" in data:
        error_str = str(data.get("error", {})).lower()
        if "access" in error_str or "permission" in error_str:
            # Try to list accessible accounts for helpful error message
            accessible_accounts = await _get_accounts_api_call()

            if accessible_accounts.get("data"):
                accessible_accounts: List[Dict[str, Any]] = [
                    {"id": act["id"], "name": act["name"]}
                    for act in accessible_accounts["data"][:10]
                ]
                return APIToolErrors.account_not_accessible(account_id, accessible_accounts).to_json()
        return json.dumps(data, indent=2)
    
    # DSA requirement details
    """
    DSA (Digital Services Act) is a European Union regulation that requires certain businesses to comply with certain requirements.
    """
    if "business_country_code" in data:
        european_countries = ["DE", "FR", "IT", "ES", "NL", "BE", "AT", "IE", "DK", "SE", "FI", "NO"]
        if data["business_country_code"] in european_countries:
            data["dsa_required"] = True
            data["dsa_compliance_note"] = "This account is subject to European DSA (Digital Services Act) requirements"
        else:
            data["dsa_required"] = False
            data["dsa_compliance_note"] = "This account is not subject to European DSA requirements"
    
    return data 


