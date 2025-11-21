"""
Mete Ads Creative Tools.
Format which provides layout and contains content for the ad.
Cite from: https://developers.facebook.com/docs/marketing-api/reference/ad-creative
Ctie from: https://developers.facebook.com/docs/marketing-api/reference/ad-account/adcreatives

- get_creative_by_account: Get ad creatives for a Meta Ads account.
- get_creatives_by_ad: Get ad creatives associated with a Meta Ads ad.
- get_creative_details: Get details of a creative.
- create_creative: Create a new ad creative using an uploaded image hash.
- update_ad_creative: Update an existing ad creative with new content or settings.

Internal helper functions:
- _get_creative_details: Internal function to get details of a creative.
- _validate_headline_descriptions: Validate headlines and descriptions.
- _extract_creative_image_urls: Extract image URLs from a creative object for direct viewing.
"""
from typing import Optional, Dict, Any, List
import json
from datetime import datetime

from langchain.tools import tool

from ithaca.logger import logger
from ithaca.tools.meta_api.meta_ads_api import make_api_request, meta_api_tool
from ithaca.tools.meta_api.utils import APIToolErrors, valid_account_id
from ithaca.tools.meta_api.utils import STATUS_VALIDATOR
from ithaca.tools.meta_api.meta_ads_page import _discover_pages_for_account


@tool
@meta_api_tool
async def get_creative_by_account(
    account_id: str,
    access_token: Optional[str] = None
) -> str:
    """
    Get ad creatives for a Meta Ads account.
    The query fields are: "id,name,status,thumbnail_url,image_url,image_hash,object_story_spec,asset_feed_spec,image_urls_for_viewing"
    
    Args:
        account_id: Meta Ads account ID
        access_token: Meta API access token (optional - will use cached token if not provided)
    """
    if not account_id:
        return APIToolErrors.no_account_id().to_json()
    account_id = valid_account_id(account_id)
    endpoint = f"{account_id}/adcreatives"
    params = {
        "fields": "id,name,status,thumbnail_url,image_url,image_hash,object_story_spec,asset_feed_spec,image_urls_for_viewing"
    }
    
    data = await make_api_request(endpoint, access_token, params)
    if "data" in data:
        for creative in data["data"]:
            creative["image_urls_for_viewing"] = _extract_creative_image_urls(creative)
    
    return json.dumps(data, indent=2)


@tool
@meta_api_tool
async def get_creatives_by_ad(
    ad_id: str,
    access_token: Optional[str] = None
) -> str:
    """
    Get ad creatives associated with a Meta Ads ad.
    The query fields are: "id,name,status,thumbnail_url,image_url,image_hash,object_story_spec,asset_feed_spec,image_urls_for_viewing"
    
    Args:
        ad_id: Meta Ads ad ID
        access_token: Meta API access token (optional - will use cached token if not provided)
    """
    if not ad_id:
        return APIToolErrors.arg_missing("ad_id", "str", "Ad ID is required").to_json()
    endpoint = f"{ad_id}/adcreatives"
    params = {
        "fields": "id,name,status,thumbnail_url,image_url,image_hash,object_story_spec,asset_feed_spec,image_urls_for_viewing"
    }

    data = await make_api_request(endpoint, access_token, params)
    if "data" in data:
        for creative in data["data"]:
            creative["image_urls_for_viewing"] = _extract_creative_image_urls(creative)
    
    return json.dumps(data, indent=2)


@tool
@meta_api_tool
async def get_creative_details(
    creative_id: str,
    access_token: Optional[str] = None
) -> str:
    """
    Get details of a creative.
    The query fields are: "id,name,status,thumbnail_url,image_url,image_hash,object_story_spec,asset_feed_spec,url_tags,link_url,dynamic_creative_spec"
    """
    if not creative_id:
        return APIToolErrors.arg_missing("creative_id", "str", "Creative ID is required").to_json()
    data = await _get_creative_details(creative_id, access_token)
    if "data" in data:
        data["data"]["image_urls_for_viewing"] = _extract_creative_image_urls(data["data"])
    return json.dumps(data, indent=2)


@tool
@meta_api_tool
async def create_creative(
    account_id: str,
    image_hash: str,
    creative_name: Optional[str] = None,
    page_id: Optional[str] = None,
    link_url: Optional[str] = None,
    message: Optional[str] = None,
    headline: Optional[str] = None,
    headlines: Optional[List[str]] = None,
    description: Optional[str] = None,
    descriptions: Optional[List[str]] = None,
    dynamic_creative_spec: Optional[Dict[str, Any]] = None,
    call_to_action_type: Optional[str] = None,
    instagram_actor_id: Optional[str] = None,
    access_token: Optional[str] = None,
) -> str:
    """
    Create a new ad creative using an uploaded image hash.

    Args:
        account_id (str): Meta Ads account ID
        image_hash (str): Hash of the uploaded image
        creative_name (Optional[str]): Creative name
        page_id (Optional[str]): Facebook Page ID to be used for the ad
        link_url (Optional[str]): Destination URL for the ad
        message (Optional[str]): Ad copy/text
        headline (Optional[str]): Single headline for simple ads (cannot be used with headlines)
        headlines (Optional[List[str]]): List of headlines for dynamic creative testing (cannot be used with headline), each headline must be less than or equal to 40 characters, and the number of headlines must be less than or equal to 5
        description (Optional[str]): Single description for simple ads (cannot be used with descriptions)
        descriptions (Optional[List[str]]): List of descriptions for dynamic creative testing (cannot be used with description), each description must be less than or equal to 125 characters, and the number of descriptions must be less than or equal to 5
        dynamic_creative_spec (Optional[Dict[str, Any]]): Dynamic creative optimization settings
        call_to_action_type (Optional[str]): Call to action button type (e.g., 'LEARN_MORE', 'SIGN_UP', 'SHOP_NOW')
        instagram_actor_id (Optional[str]): Optional Instagram account ID for Instagram placements
        access_token (Optional[str]): Meta API access token (optional - will use cached token if not provided)

    Returns:
        JSON response with created creative details
    """
    if not account_id:
        return APIToolErrors.no_account_id().to_json()
    account_id = valid_account_id(account_id)

    if not image_hash:
        return APIToolErrors.arg_missing("image_hash", "str", "Image hash is required").to_json()
    
    if not creative_name:
        creative_name = f"Ad Creative at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    # page_id is required:
    if not page_id:
        try:
            page_discovery_result = await _discover_pages_for_account(account_id, access_token)
            if page_discovery_result.get("success"):
                page_id = page_discovery_result["page_id"]
                page_name = page_discovery_result["page_name"]
                logger.info(f"Automatically discovered page ID {page_id} for account {account_id} with name {page_name}")
            else:
                return APIToolErrors.api_call_error(
                    message="No page ID provided and failed to discover pages for account, please provide page_id manually or use get_pages_for_account tool to see all available pages",
                    details=json.dumps(page_discovery_result, indent=2),
                    params_sent={"account_id": account_id},
                ).to_json()
        except Exception as e:
            return APIToolErrors.api_call_error(
                message="No page ID provided and failed to discover pages for account, please provide page_id manually or use get_pages_for_account tool to see all available pages",
                details=str(e),
                params_sent={"account_id": account_id},
            ).to_json()
    
    # validate headline/headlines and description/descriptions
    validation_error = _validate_headline_descriptions(headline, headlines, description, descriptions)
    if validation_error:
        return validation_error
    
    endpoint = f"{account_id}/adcreatives"
    params = {
        "name": creative_name,
    }

    # Either dynamic creative or traditional creative
    # Dynamic creative: headlines and descriptions are required, asset_feed_spec
    # Traditional creative: headline and description, object_story_spec
    if headlines or descriptions:
        asset_feed_spec = {
            "ad_formats": ["SINGLE_IMAGE"],
            "images": [{"hash": image_hash}],
            "link_urls": [{"website_url": link_url if link_url else "https://facebook.com"}],
        }

        # Handle headlines
        if headlines:
            asset_feed_spec["headlines"] = [{"text": headline_text} for headline_text in headlines]
            
        # Handle descriptions  
        if descriptions:
            asset_feed_spec["descriptions"] = [{"text": description_text} for description_text in descriptions]
        
        # Add message as primary_texts if provided
        if message:
            asset_feed_spec["primary_texts"] = [{"text": message}]
        
        # Add call_to_action_types if provided
        if call_to_action_type:
            asset_feed_spec["call_to_action_types"] = [call_to_action_type]
        
        params["asset_feed_spec"] = asset_feed_spec
        
        # For dynamic creatives, we need a simplified object_story_spec
        params["object_story_spec"] = {
            "page_id": page_id
        }
    else:
        params["object_story_spec"] = {
            "page_id": page_id,
            "link_data": {
                "image_hash": image_hash,
                "link": link_url if link_url else "https://facebook.com"
            }
        }

        if message:
            params["object_story_spec"]["link_data"]["message"] = message
        
        if creative_name:
            params["object_story_spec"]["link_data"]["name"] = creative_name
        
        if description:
            params["object_story_spec"]["link_data"]["description"] = description
        
        if call_to_action_type:
            params["object_story_spec"]["link_data"]["call_to_action_type"] = {"type": call_to_action_type}
    
    # Add dynamic creative spec if provided
    if dynamic_creative_spec:
        params["dynamic_creative_spec"] = dynamic_creative_spec
    
    if instagram_actor_id:
        params["instagram_actor_id"] = instagram_actor_id
    
    try:
        data = await make_api_request(endpoint, access_token, params, method="POST")

        if "id" in data:
            creative_id = data["id"]
            creative_details = await _get_creative_details(creative_id ,access_token)
            return json.dumps({
                "success": True,
                "creative_id": creative_id,
                "details": creative_details
            }, indent=2)
        
        return json.dumps(data, indent=2)
    
    except Exception as e:
        return APIToolErrors.api_call_error(
            message="Failed to create creative",
            details=str(e),
            params_sent=params,
        ).to_json()


@tool
@meta_api_tool
async def update_creative(
    creative_id: str,
    access_token: Optional[str] = None,
    creative_name: Optional[str] = None,
    message: Optional[str] = None,
    headline: Optional[str] = None,
    headlines: Optional[List[str]] = None,
    description: Optional[str] = None,
    descriptions: Optional[List[str]] = None,
    dynamic_creative_spec: Optional[Dict[str, Any]] = None,
    call_to_action_type: Optional[str] = None
) -> str:
    """
    Update an existing ad creative with new content or settings.
    
    Args:
        creative_id: Meta Ads creative ID to update
        access_token: Meta API access token (optional - will use cached token if not provided)
        creative_name: New creative name
        message: New ad copy/text
        headline: Single headline for simple ads (cannot be used with headlines)
        headlines: New list of headlines for dynamic creative testing (cannot be used with headline)
        description: Single description for simple ads (cannot be used with descriptions)
        descriptions: New list of descriptions for dynamic creative testing (cannot be used with description)
        dynamic_creative_spec: New dynamic creative optimization settings
        call_to_action_type: New call to action button type
    
    Returns:
        JSON response with updated creative details
    """
    # Check required parameters
    if not creative_id:
        return APIToolErrors.arg_missing("creative_id", "str", "Creative ID is required").to_json()
    
    # validate headline/headlines and description/descriptions
    validation_error = _validate_headline_descriptions(headline, headlines, description, descriptions)
    if validation_error:
        return validation_error
    
    endpoint = f"{creative_id}"
    params = {}
    
    if creative_name:
        params["name"] = creative_name
    
    # Choose between asset_feed_spec (dynamic creative) or object_story_spec (traditional)
    # ONLY use asset_feed_spec when user explicitly provides plural parameters (headlines/descriptions)
    if headlines or descriptions or dynamic_creative_spec:
        # Handle dynamic creative assets via asset_feed_spec
        asset_feed_spec = {}
        
        # Add required ad_formats field for dynamic creatives
        asset_feed_spec["ad_formats"] = ["SINGLE_IMAGE"]
        
        # Handle headlines
        if headlines:
            asset_feed_spec["headlines"] = [{"text": headline_text} for headline_text in headlines]
            
        # Handle descriptions  
        if descriptions:
            asset_feed_spec["descriptions"] = [{"text": description_text} for description_text in descriptions]
        
        # Add message as primary_texts if provided
        if message:
            asset_feed_spec["primary_texts"] = [{"text": message}]
        
        # Add call_to_action_types if provided
        if call_to_action_type:
            asset_feed_spec["call_to_action_types"] = [call_to_action_type]
        
        params["asset_feed_spec"] = asset_feed_spec
    else:
        # Use traditional object_story_spec with link_data for simple creatives
        if message or headline or description or call_to_action_type:
            params["object_story_spec"] = {"link_data": {}}
            
            if message:
                params["object_story_spec"]["link_data"]["message"] = message
            
            # Add headline (singular) to link_data
            if headline:
                params["object_story_spec"]["link_data"]["name"] = headline
            
            # Add description (singular) to link_data
            if description:
                params["object_story_spec"]["link_data"]["description"] = description
            
            # Add call_to_action to link_data for simple creatives
            if call_to_action_type:
                params["object_story_spec"]["link_data"]["call_to_action"] = {
                    "type": call_to_action_type
                }
    
    # Add dynamic creative spec if provided
    if dynamic_creative_spec:
        params["dynamic_creative_spec"] = dynamic_creative_spec
    
    try:
        # Make API request to update the creative
        data = await make_api_request(endpoint, access_token, params, method="POST")
        
        # If successful, get more details about the updated creative
        if "id" in data:
            creative_details = await _get_creative_details(creative_id, access_token)
            return json.dumps({
                "success": True,
                "creative_id": creative_id,
                "details": creative_details
            }, indent=2)
        
        return json.dumps(data, indent=2)
    
    except Exception as e:
        return APIToolErrors.api_call_error(
            message=f"Failed to update creative: {creative_id}",
            details=str(e),
            params_sent=params,
        ).to_json()


@tool
@meta_api_tool
async def delete_creative(
    creative_id: str,
    access_token: Optional[str],
) -> str:
    """
    Delete an existing Meta Ads creative.
    
    Args:
        creative_id: Meta Ads creative ID to delete
        access_token: Meta API access token (optional - will use cached token if not provided)
    """
    if not creative_id:
        return APIToolErrors.arg_missing("creative_id", "str", "Creative ID is required").to_json()
    endpoint = f"{creative_id}"
    try:
        data = await make_api_request(endpoint, access_token, None, method="DELETE")
        return json.dumps(data, indent=2)
    except Exception as e:
        return APIToolErrors.api_call_error(
            message=f"Failed to delete creative: {creative_id}",
            details=str(e),
            params_sent={},
        ).to_json()


# Internal helper functions
async def _get_creative_details(creative_id: str, access_token: Optional[str] = None) -> Dict[str, Any]:
    """
    Internal function to get details of a creative.
    The query fields are: "id,name,status,thumbnail_url,image_url,image_hash,object_story_spec,asset_feed_spec,url_tags,link_url,dynamic_creative_spec"
    
    Args:
        creative_id: Meta Ads creative ID
        access_token: Meta API access token (optional - will use cached token if not provided)
    
    Returns:
        Dict with creative details
    """
    endpoint = f"{creative_id}"
    params = {
        "fields": "id,name,status,thumbnail_url,image_url,image_hash,object_story_spec,asset_feed_spec,url_tags,link_url,dynamic_creative_spec"
    }
    data = await make_api_request(endpoint, access_token, params)
    return data


def _validate_headline_descriptions(
    headline: Optional[str] = None, 
    headlines: Optional[List[str]] = None, 
    description: Optional[str] = None, 
    descriptions: Optional[List[str]] = None
) -> Optional[str]:
    """
    Internal function to validate headlines and descriptions.
    """
    if headline and headlines:
        return APIToolErrors.error(
            message="Can not use both 'headline' and 'headlines' parameters at the same time"
        ).to_json()
    
    if headlines:
        if len(headlines) > 5:
            return APIToolErrors.error(
                message=f"The number of headlines must be less than or equal to 5, got {len(headlines)} headlines"
            ).to_json()
        for idx, headline in enumerate(headlines):
            if len(headline) > 40:
                return APIToolErrors.error(
                    message=f"Headline {idx+1}: '{headline}' is too long, it must be less than or equal to 40 characters"
                ).to_json()
    
    if description and descriptions:
        return APIToolErrors.error(
            message="Can not use both 'description' and 'descriptions' parameters at the same time",
        ).to_json()
    
    if descriptions:
        if len(descriptions) > 5:
            return APIToolErrors.error(
                message=f"The number of descriptions must be less than or equal to 5, got {len(descriptions)} descriptions"
            ).to_json()
        for idx, description in enumerate(descriptions):
            if len(description) > 125:
                return APIToolErrors.error(
                    message=f"Description {idx+1}: '{description}' is too long, it must be less than or equal to 125 characters"
                ).to_json()
    return None


def _extract_creative_image_urls(creative: Dict[str, Any]) -> List[str]:
    """
    Internal function to extract image URLs from a creative object for direct viewing.
    Prioritizes higher quality images over thumbnails.
    
    Args:
        creative: Meta Ads creative object
        
    Returns:
        List of image URLs found in the creative, prioritized by quality
    """
    image_urls = []
    
    # Prioritize higher quality image URLs in this order:
    # 1. image_urls_for_viewing (usually highest quality)
    # 2. image_url (direct field)
    # 3. object_story_spec.link_data.picture (usually full size)
    # 4. asset_feed_spec images (multiple high-quality images)
    # 5. thumbnail_url (last resort - often profile thumbnail)
    
    # Check for image_urls_for_viewing (highest priority)
    if "image_urls_for_viewing" in creative and creative["image_urls_for_viewing"]:
        image_urls.extend(creative["image_urls_for_viewing"])
    
    # Check for direct image_url field
    if "image_url" in creative and creative["image_url"]:
        image_urls.append(creative["image_url"])
    
    # Check object_story_spec for image URLs
    if "object_story_spec" in creative:
        story_spec = creative["object_story_spec"]
        
        # Check link_data for image fields
        if "link_data" in story_spec:
            link_data = story_spec["link_data"]
            
            # Check for picture field (usually full size)
            if "picture" in link_data and link_data["picture"]:
                image_urls.append(link_data["picture"])
                
            # Check for image_url field in link_data
            if "image_url" in link_data and link_data["image_url"]:
                image_urls.append(link_data["image_url"])
        
        # Check video_data for thumbnail (if present)
        if "video_data" in story_spec and "image_url" in story_spec["video_data"]:
            image_urls.append(story_spec["video_data"]["image_url"])
    
    # Check asset_feed_spec for multiple images
    if "asset_feed_spec" in creative and "images" in creative["asset_feed_spec"]:
        for image in creative["asset_feed_spec"]["images"]:
            if "url" in image and image["url"]:
                image_urls.append(image["url"])
    
    # Check for thumbnail_url field (lowest priority)
    if "thumbnail_url" in creative and creative["thumbnail_url"]:
        image_urls.append(creative["thumbnail_url"])
    
    # Remove duplicates while preserving order
    seen = set()
    unique_urls = []
    for url in image_urls:
        if url not in seen:
            seen.add(url)
            unique_urls.append(url)
    
    return unique_urls