"""
Meta Ads page tools.
Page represents a Facebook page, which is the identity of an advertiser on Facebook.
Page can not be created by API.
Cite from: https://developers.facebook.com/docs/graph-api/reference/page/#Creating

- get_pages_for_account: get pages associated with a Meta Ads account
- search_pages_by_name: search pages by name within an account
"""
from typing import Optional, Dict, Any, List
import json
import asyncio

from langchain.tools import tool

from ithaca.tools.meta_api.meta_ads_api import make_api_request, meta_api_tool
from ithaca.tools.meta_api.utils import APIToolErrors, valid_account_id, concise_return_message
from ithaca.tools.meta_api.utils import STATUS_VALIDATOR


def get_pages_for_account_tool(
    account_id: str = "me"
) -> str:
    """
    Get pages associated with a Meta Ads account.

    Args:
        account_id: Meta Ads account ID or "me" for the current user
        access_token: Meta API access token (optional - will use cached token if not provided)
    """
    return asyncio.run(_get_pages_for_account_kernel(account_id))


@meta_api_tool
async def _get_pages_for_account_kernel(
    account_id: str,
    access_token: Optional[str] = None,
):
    if not account_id:
        return json.dumps({"error": "No account ID provided"}, indent=2)
    
    # Handle special case for 'me' (current user)
    if account_id == "me":
        try:
            endpoint = "me/accounts"
            params = {
                "fields": "id,name,username,category,fan_count,link,verification_status,picture"
            }
            
            user_pages_data = await make_api_request(endpoint, access_token, params)
            return concise_return_message(user_pages_data, params)
        except Exception as e:
            return APIToolErrors.api_call_error(
                message="Failed to get user pages",
                details=str(e),
                params_sent={"account_id": account_id},
            ).to_json()
    
    account_id = valid_account_id(account_id)
    
    try:
        # Collect all page IDs from multiple approaches
        all_page_ids = set()
        
        # Approach 1: Get user's personal pages (broad scope)
        try:
            endpoint = "me/accounts"
            params = {
                "fields": "id,name,username,category,fan_count,link,verification_status,picture"
            }
            user_pages_data = await make_api_request(endpoint, access_token, params)
            if "data" in user_pages_data:
                for page in user_pages_data["data"]:
                    if "id" in page:
                        all_page_ids.add(page["id"])
        except Exception:
            pass
        
        # Approach 2: Try business manager pages
        try:
            # Strip 'act_' prefix to get raw account ID for business endpoints
            raw_account_id = account_id.replace("act_", "")
            endpoint = f"{raw_account_id}/owned_pages"
            params = {
                "fields": "id,name,username,category,fan_count,link,verification_status,picture"
            }
            business_pages_data = await make_api_request(endpoint, access_token, params)
            if "data" in business_pages_data:
                for page in business_pages_data["data"]:
                    if "id" in page:
                        all_page_ids.add(page["id"])
        except Exception:
            pass
        
        # Approach 3: Try ad account client pages
        try:
            endpoint = f"{account_id}/client_pages"
            params = {
                "fields": "id,name,username,category,fan_count,link,verification_status,picture"
            }
            client_pages_data = await make_api_request(endpoint, access_token, params)
            if "data" in client_pages_data:
                for page in client_pages_data["data"]:
                    if "id" in page:
                        all_page_ids.add(page["id"])
        except Exception:
            pass
        
        # Approach 4: Extract page IDs from all ad creatives (broader creative search)
        try:
            endpoint = f"{account_id}/adcreatives"
            params = {
                "fields": "id,name,object_story_spec,link_url,call_to_action,image_hash",
                "limit": 100
            }
            creatives_data = await make_api_request(endpoint, access_token, params)
            if "data" in creatives_data:
                for creative in creatives_data["data"]:
                    if "object_story_spec" in creative and "page_id" in creative["object_story_spec"]:
                        all_page_ids.add(creative["object_story_spec"]["page_id"])
        except Exception:
            pass
            
        # Approach 5: Get active ads and extract page IDs from creatives
        try:
            endpoint = f"{account_id}/ads"
            params = {
                "fields": "creative{object_story_spec{page_id},link_url,call_to_action}",
                "limit": 100
            }
            ads_data = await make_api_request(endpoint, access_token, params)
            if "data" in ads_data:
                for ad in ads_data.get("data", []):
                    if "creative" in ad and "object_story_spec" in ad["creative"] and "page_id" in ad["creative"]["object_story_spec"]:
                        all_page_ids.add(ad["creative"]["object_story_spec"]["page_id"])
        except Exception:
            pass

        # Approach 6: Try promoted_objects endpoint
        try:
            endpoint = f"{account_id}/promoted_objects"
            params = {
                "fields": "page_id,object_store_url,product_set_id,application_id"
            }
            promoted_objects_data = await make_api_request(endpoint, access_token, params)
            if "data" in promoted_objects_data:
                for obj in promoted_objects_data["data"]:
                    if "page_id" in obj:
                        all_page_ids.add(obj["page_id"])
        except Exception:
            pass

        # Approach 7: Extract page IDs from tracking_specs in ads (most reliable)
        try:
            endpoint = f"{account_id}/ads"
            params = {
                "fields": "id,name,status,creative,tracking_specs",
                "limit": 100
            }
            tracking_ads_data = await make_api_request(endpoint, access_token, params)
            if "data" in tracking_ads_data:
                for ad in tracking_ads_data.get("data", []):
                    tracking_specs = ad.get("tracking_specs", [])
                    if isinstance(tracking_specs, list):
                        for spec in tracking_specs:
                            if isinstance(spec, dict) and "page" in spec:
                                page_list = spec["page"]
                                if isinstance(page_list, list):
                                    for page_id in page_list:
                                        if isinstance(page_id, (str, int)) and str(page_id).isdigit():
                                            all_page_ids.add(str(page_id))
        except Exception:
            pass
            
        # Approach 8: Try campaigns and extract page info
        try:
            endpoint = f"{account_id}/campaigns"
            params = {
                "fields": "id,name,promoted_object,objective",
                "limit": 50
            }
            campaigns_data = await make_api_request(endpoint, access_token, params)
            if "data" in campaigns_data:
                for campaign in campaigns_data["data"]:
                    if "promoted_object" in campaign and "page_id" in campaign["promoted_object"]:
                        all_page_ids.add(campaign["promoted_object"]["page_id"])
        except Exception:
            pass
            
        # If we found any page IDs, get details for each
        if all_page_ids:
            page_details = {
                "data": [], 
                "total_pages_found": len(all_page_ids)
            }
            
            for page_id in all_page_ids:
                try:
                    page_endpoint = f"{page_id}"
                    page_params = {
                        "fields": "id,name,username,category,fan_count,link,verification_status,picture"
                    }
                    
                    page_data = await make_api_request(page_endpoint, access_token, page_params)
                    if "id" in page_data:
                        page_details["data"].append(page_data)
                    else:
                        page_details["data"].append({
                            "id": page_id, 
                            "error": "Page details not accessible"
                        })
                except Exception as e:
                    page_details["data"].append({
                        "id": page_id,
                        "error": f"Failed to get page details: {str(e)}"
                    })
            
            if page_details["data"]:
                return json.dumps(page_details, indent=2)
        
        # If all approaches failed, return empty data with a message
        return json.dumps({
            "data": [],
            "message": "No pages found associated with this account",
            "suggestion": "Create a Facebook page and connect it to this ad account, or ensure existing pages are properly connected through Business Manager"
        }, indent=2)
        
    except Exception as e:
        return APIToolErrors.api_call_error(
            message="Failed to get account pages",
            details=str(e),
            params_sent={"account_id": account_id},
        ).to_json()


async def _discover_pages_for_account(account_id: str, access_token: Optional[str] = None) -> dict:
    """
    Internal function to discover pages for an account using multiple approaches.
    Returns the best available page ID for ad creation.

    Return schema:
        {
            "success": bool,
            "page_id": str, # The best available page ID for ad creation
            "page_name": str, # The name of the page
            "source": str, # The source of the page
            "note": str # A note about the page
        }
    
    Return example:
        {
            "success": True,
            "page_id": "1234567890",
            "page_name": "My Page",
            "source": "tracking_specs",
            "note": "Page ID extracted from existing ads - most reliable for ad creation"
        }

    Return error example:
        {
            "success": False,
            "message": "No suitable pages found for this account",
            "note": "Try using get_pages_for_account tool to see all available pages or provide page_id manually"
        }
    """
    try:
        # Approach 1: Extract page IDs from tracking_specs in ads (most reliable)
        endpoint = f"{account_id}/ads"
        params = {
            "fields": "id,name,adset_id,campaign_id,status,creative,created_time,updated_time,bid_amount,conversion_domain,tracking_specs",
            "limit": 100
        }
        
        tracking_ads_data = await make_api_request(endpoint, access_token, params)
        
        tracking_page_ids = set()
        if "data" in tracking_ads_data:
            for ad in tracking_ads_data.get("data", []):
                tracking_specs = ad.get("tracking_specs", [])
                if isinstance(tracking_specs, list):
                    for spec in tracking_specs:
                        if isinstance(spec, dict) and "page" in spec:
                            page_list = spec["page"]
                            if isinstance(page_list, list):
                                for page_id in page_list:
                                    if isinstance(page_id, (str, int)) and str(page_id).isdigit():
                                        tracking_page_ids.add(str(page_id))
        
        if tracking_page_ids:
            # Get details for the first page found
            page_id = list(tracking_page_ids)[0]
            page_endpoint = f"{page_id}"
            page_params = {
                "fields": "id,name,username,category,fan_count,link,verification_status,picture"
            }
            
            page_data = await make_api_request(page_endpoint, access_token, page_params)
            if "id" in page_data:
                return {
                    "success": True,
                    "page_id": page_id,
                    "page_name": page_data.get("name", "Unknown"),
                    "source": "tracking_specs",
                    "note": "Page ID extracted from existing ads - most reliable for ad creation"
                }
        
        # Approach 2: Try client_pages endpoint
        endpoint = f"{account_id}/client_pages"
        params = {
            "fields": "id,name,username,category,fan_count,link,verification_status,picture"
        }
        
        client_pages_data = await make_api_request(endpoint, access_token, params)
        
        if "data" in client_pages_data and client_pages_data["data"]:
            page = client_pages_data["data"][0]
            return {
                "success": True,
                "page_id": page["id"],
                "page_name": page.get("name", "Unknown"),
                "source": "client_pages"
            }
        
        # Approach 3: Try assigned_pages endpoint
        pages_endpoint = f"{account_id}/assigned_pages"
        pages_params = {
            "fields": "id,name",
            "limit": 1 
        }
        
        pages_data = await make_api_request(pages_endpoint, access_token, pages_params)
        
        if "data" in pages_data and pages_data["data"]:
            page = pages_data["data"][0]
            return {
                "success": True,
                "page_id": page["id"],
                "page_name": page.get("name", "Unknown"),
                "source": "assigned_pages"
            }
        
        # If all approaches failed
        return {
            "success": False,
            "message": "No suitable pages found for this account",
            "note": "Try using get_pages_for_account tool to see all available pages or provide page_id manually"
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Error during page discovery: {str(e)}"
        }


@meta_api_tool
async def _search_pages_by_name_core(account_id: str, search_term: Optional[str] = None, access_token: Optional[str] = None) -> str:
    """
    Core logic for searching pages by name.
    
    Args:
        account_id: Meta Ads account ID (format: act_XXXXXXXXX)
        search_term: Search term to find pages by name (optional - returns all pages if not provided)
        access_token: Meta API access token (optional - will use cached token if not provided)
    
    Returns:
        JSON string with search results
    """
    account_id = valid_account_id(account_id)
    
    try:
        # Use the internal discovery function directly
        page_discovery_result = await _discover_pages_for_account(account_id, access_token)
        
        if not page_discovery_result.get("success"):
            return json.dumps({
                "data": [],
                "message": "No pages found for this account",
                "details": page_discovery_result.get("message", "Page discovery failed")
            }, indent=2)
        
        # Create a single page result
        page_data = {
            "id": page_discovery_result["page_id"],
            "name": page_discovery_result.get("page_name", "Unknown"),
            "source": page_discovery_result.get("source", "unknown")
        }
        
        all_pages_data = {"data": [page_data]}
        
        # Filter pages by search term if provided
        if search_term:
            search_term_lower = search_term.lower()
            filtered_pages = []
            
            for page in all_pages_data["data"]:
                page_name = page.get("name", "").lower()
                if search_term_lower in page_name:
                    filtered_pages.append(page)
            
            return json.dumps({
                "data": filtered_pages,
                "search_term": search_term,
                "total_found": len(filtered_pages),
                "total_available": len(all_pages_data["data"])
            }, indent=2)
        else:
            # Return all pages if no search term provided
            return json.dumps({
                "data": all_pages_data["data"],
                "total_available": len(all_pages_data["data"]),
                "note": "Use search_term parameter to filter pages by name"
            }, indent=2)
    
    except Exception as e:
        return APIToolErrors.api_call_error(
            message="Failed to search pages by name",
            details=str(e),
            params_sent={"account_id": account_id, "search_term": search_term},
        ).to_json()


@tool
async def search_pages_by_name(
    account_id: str,
    search_term: Optional[str] = None
) -> str:
    """
    Search for pages by name within an account.
    
    Args:
        account_id: Meta Ads account ID (format: act_XXXXXXXXX)
        search_term: Search term to find pages by name (optional - returns all pages if not provided)
    
    Returns:
        JSON response with matching pages
    """
    if not account_id:
        return APIToolErrors.no_account_id().to_json()
    result = await _search_pages_by_name_core(account_id, search_term)
    return result


def get_pages_by_name_tool(
    account_id: str,
    search_term: str,
) -> dict:
    return asyncio.run(_search_pages_by_name_core(account_id, search_term))


# TODO: clean up internal functions to get pages for a Meta Ads account
