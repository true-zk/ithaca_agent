"""
    Core API functionality for Meta Ads API.
    Cite from: https://github.com/pipeboard-co/meta-ads-mcp/blob/main/meta_ads_mcp/core/api.py
"""
from curses import meta
from typing import Any, Dict, Optional, Callable
import json
import httpx
import asyncio
import functools
import os

from ithaca.oauth.auth import auth_manager
from ithaca.logger import logger
from ithaca.settings import META_GRAPH_API_VERSION, META_GRAPH_API_BASE, USER_AGENT


# Log key environment and configuration at startup
logger.info("Core API module initialized")
logger.info(f"Graph API Version: {META_GRAPH_API_VERSION}")
logger.info(f"META_APP_ID env var present: {'Yes' if os.environ.get('META_APP_ID') else 'No'}")

class GraphAPIError(Exception):
    """Exception raised for errors from the Graph API."""
    def __init__(self, error_data: Dict[str, Any]):
        self.error_data = error_data
        self.message = error_data.get('message', 'Unknown Graph API error')
        super().__init__(self.message)
        
        # Log error details
        logger.error(f"Graph API Error: {self.message}")
        logger.debug(f"Error details: {error_data}")
        
        # Check if this is an auth error
        if "code" in error_data and error_data["code"] in [190, 102, 4]:
            # Common auth error codes
            logger.warning(f"Auth error detected (code: {error_data['code']}). Invalidating token.")
            # auth_manager.invalidate_token()


async def make_api_request(
    endpoint: str,
    access_token: str,
    params: Optional[Dict[str, Any]] = None,
    method: str = "GET"
) -> Dict[str, Any]:
    """
    Make a request to the Meta Graph API.
    
    Args:
        endpoint: API endpoint path (without base URL)
        access_token: Meta API access token
        params: Additional query parameters
        method: HTTP method (GET, POST, DELETE)
    
    Returns:
        API response as a dictionary
    """
    # Validate access token before proceeding
    if not access_token:
        logger.error("API request attempted with blank access token")
        return {
            "error": {
                "message": "Authentication Required",
                "details": "A valid access token is required to access the Meta API",
                "action_required": "Please authenticate first"
            }
        }
        
    url = f"{META_GRAPH_API_BASE}/{endpoint}"
    
    headers = {
        "User-Agent": USER_AGENT,
    }
    
    request_params = params or {}
    request_params["access_token"] = access_token
    
    # Logging the request (masking token for security)
    masked_params = {k: "***TOKEN***" if k == "access_token" else v for k, v in request_params.items()}
    logger.debug(f"API Request: {method} {url}")
    logger.debug(f"Request params: {masked_params}")
    
    # Check for app_id in params
    app_id = auth_manager.app_id
    logger.debug(f"Current app_id from auth_manager: {app_id}")
    
    async with httpx.AsyncClient() as client:
        try:
            if method == "GET":
                # For GET, JSON-encode dict/list params (e.g., targeting_spec) to proper strings
                encoded_params = {}
                for key, value in request_params.items():
                    if isinstance(value, (dict, list)):
                        encoded_params[key] = json.dumps(value)
                    else:
                        encoded_params[key] = value
                response = await client.get(url, params=encoded_params, headers=headers, timeout=30.0)
            elif method == "POST":
                # For Meta API, POST requests need data, not JSON
                if 'targeting' in request_params and isinstance(request_params['targeting'], dict):
                    # Convert targeting dict to string for the API
                    request_params['targeting'] = json.dumps(request_params['targeting'])
                
                # Convert lists and dicts to JSON strings    
                for key, value in request_params.items():
                    if isinstance(value, (list, dict)):
                        request_params[key] = json.dumps(value)
                
                logger.debug(f"POST params (prepared): {masked_params}")
                response = await client.post(url, data=request_params, headers=headers, timeout=30.0)
            elif method == "DELETE":
                response = await client.delete(url, params=request_params, headers=headers, timeout=30.0)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            logger.debug(f"API Response status: {response.status_code}")
            
            # Ensure the response is JSON and return it as a dictionary
            try:
                return response.json()
            except json.JSONDecodeError:
                # If not JSON, return text content in a structured format
                return {
                    "text_response": response.text,
                    "status_code": response.status_code
                }
        
        except httpx.HTTPStatusError as e:
            error_info = {}
            try:
                error_info = e.response.json()
            except:
                error_info = {"status_code": e.response.status_code, "text": e.response.text}
            
            logger.error(f"HTTP Error: {e.response.status_code} - {error_info}")
            
            # Check for authentication errors
            if e.response.status_code == 401 or e.response.status_code == 403:
                logger.warning("Detected authentication error (401/403)")
                auth_manager.invalidate_token()
            elif "error" in error_info:
                error_obj = error_info.get("error", {})
                # Check for specific FB API errors related to auth
                if isinstance(error_obj, dict) and error_obj.get("code") in [190, 102, 4, 200, 10]:
                    logger.warning(f"Detected Facebook API auth error: {error_obj.get('code')}")
                    # Log more details about app ID related errors
                    if error_obj.get("code") == 200 and "Provide valid app ID" in error_obj.get("message", ""):
                        logger.error("Meta API authentication configuration issue")
                        logger.error(f"Current app_id: {app_id}")
                        # Provide a clearer error message without the confusing "Provide valid app ID" message
                        return {
                            "error": {
                                "message": "Meta API authentication configuration issue. Please check your app credentials.",
                                "original_error": error_obj.get("message"),
                                "code": error_obj.get("code")
                            }
                        }
                    auth_manager.invalidate_token()
            
            # Include full details for technical users
            full_response = {
                "headers": dict(e.response.headers),
                "status_code": e.response.status_code,
                "url": str(e.response.url),
                "reason": getattr(e.response, "reason_phrase", "Unknown reason"),
                "request_method": e.request.method,
                "request_url": str(e.request.url)
            }
            
            # Return a properly structured error object
            return {
                "error": {
                    "message": f"HTTP Error: {e.response.status_code}",
                    "details": error_info,
                    "full_response": full_response
                }
            }
        
        except Exception as e:
            logger.error(f"Request Error: {str(e)}")
            return {"error": {"message": str(e)}}


def meta_api_tool(func):
    """
        Decorator for Meta API tools.
        This decorator will check access token and handle errors.
    """
    @functools.wraps(func)
    # tools are async functions
    async def wrapper(*args, **kwargs) -> str:
        # 1. check access token, if not, fetch from auth_manager
        if "access_token" not in kwargs or not kwargs["access_token"]:
            access_token = auth_manager.get_access_token()  # if not None, is valid token
            if access_token:
                kwargs["access_token"] = access_token
                logger.info(f"Use access token in auth_manager: {access_token[:10]}...")
            else:
                logger.error("No access token found, trying to authenticate")
                return None
        
        # 2. call
        result = await func(*args, **kwargs)

        # 3. handle result, make sure return a json string
        # If result is string, try to 
        if isinstance(result, str):
            try:
                result = json.loads(result)
                if "error" in result:
                    logger.error(f"API Error: {result['error']}")
                    return json.dumps(result, indent=2)
            except json.JSONDecodeError:
                return json.dumps({"data": result}, indent=2)

        if isinstance(result, dict) and "error" in result:
            return json.dumps(result, indent=2)
        
        return result

    return wrapper


# TODO: I added this tool for common API call, 
# TODO: but we need to improve it later.
@meta_api_tool
async def common_api_call_tool(
    endpoint: str,
    access_token: Optional[str] = None,
    params: Optional[Dict[str, Any]] = None,
    method: str = "GET"
) -> Dict[str, Any]:
    """
    Common API call tool.
    This tool is used to call any Meta Ads API endpoint.

    Args:
        endpoint: API endpoint path (without base URL)
        access_token: Meta API access token (optional - will use cached token if not provided)
        params: Additional query parameters
        method: HTTP method (GET, POST, DELETE)

    Returns:
        API response as a dictionary
    """
    return await make_api_request(endpoint, access_token, params, method)