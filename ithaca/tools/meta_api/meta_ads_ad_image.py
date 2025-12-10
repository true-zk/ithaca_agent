"""
Meta Ads Ad Image Tools.
Since langchain tools only support string return, 
tools should not return image bytes but a base64 encoded string of the image.

TODO: support persistent cache of the image os we don't need to download it every time.

- get_ad_image: get the image for a specific Meta Ads ad
- upload_ad_image: upload an image to a Meta Ads account from image data or image URL
"""
from typing import Optional, Dict, Any
import json
import httpx
import io
import os
from PIL import Image
import base64
import asyncio

from langchain.tools import tool
from pydantic.v1 import NoneIsAllowedError

from ithaca.logger import logger
from ithaca.tools.meta_api.meta_ads_api import make_api_request, meta_api_tool
from ithaca.tools.meta_api.utils import APIToolErrors, valid_account_id
from ithaca.tools.meta_api.meta_ads_creative import get_creatives_by_ad


@tool
async def get_ad_image(
    ad_id: str,
) -> str:
    """
    Get the image for a specific Meta Ads ad.
    Return format: {"type": "image", "base64": image_base64, "mime_type": "image/jpeg"}
    
    Args:
        ad_id: Meta Ads ad ID
        access_token: Meta API access token (optional - will use cached token if not provided)
    """
    return await _get_ad_image_kernel(ad_id)


def get_ad_image_tool(
    ad_id: str,
) -> str:
    """
    Get the image for a specific Meta Ads ad.
    Return format: {"type": "image", "base64": image_base64, "mime_type": "image/jpeg"}
    
    Args:
        ad_id: Meta Ads ad ID
        access_token: Meta API access token (optional - will use cached token if not provided)
    """
    return asyncio.run(_get_ad_image_kernel(ad_id))


@meta_api_tool
async def _get_ad_image_kernel(
    ad_id: str,
    access_token: Optional[str] = None,
) -> str:
    if not ad_id:
        return APIToolErrors.arg_missing("ad_id", "str", "Ad ID is required").to_json()

    # 1. get ad creative and ad account id
    endpoint = f"{ad_id}"
    params = {
        "fields": "creative{id},account_id"
    }
    data  = await make_api_request(endpoint, access_token, params)

    if "error" in data:
        return APIToolErrors.api_call_error(
            message=f"Failed to get ad data for ad image: {ad_id}",
            details=json.dumps(data, indent=2),
        ).to_json()
    
    account_id = data.get("account_id", "")
    if not account_id:
        return APIToolErrors.api_call_error(f"No account ID found for ad {ad_id}")
    
    if "creative" not in data:
        return APIToolErrors.api_call_error(f"No creative found for ad {ad_id}")
    
    creative_details = data.get("creative", {})
    creative_id = creative_details.get("id", "")
    if not creative_id:
        return APIToolErrors.api_call_error(f"No creative ID found for ad {ad_id}")
    
    # 2. get current creative details to find image hash
    endpoint = f"{creative_id}"
    params = {
        "fields": "id,name,image_hash,asset_feed_spec"
    }
    data = await make_api_request(endpoint, access_token, params)
    
    image_hashs = []
    image_url = None

    if "image_hash" in data:
        image_hashs.append(data["image_hash"])
    
    if "asset_feed_spec" in data and "images" in data["asset_feed_spec"]:
        image_hashs.extend(image["hash"] for image in data["asset_feed_spec"]["images"] if "hash" in image)
    
    # 3. if no image hashes found, try to extract from creatives
    if not image_hashs:
        creatives_data = await get_creatives_by_ad.ainvoke({"ad_id": ad_id, "access_token": access_token})
        creatives_data = json.loads(creatives_data)

        if "data" in creatives_data and creatives_data["data"]:
            for creative in creatives_data["data"]:
                # direct
                if "image_hash" in creative:
                    image_hashs.append(creative["image_hash"])
                # object_story_spec
                elif ("object_story_spec" in creative 
                    and "link_data" in creative["object_story_spec"]
                    and "image_hash" in creative["object_story_spec"]["link_data"]):
                    image_hashs.append(creative["object_story_spec"]["link_data"]["image_hash"])
                # asset_feed_spec
                elif "asset_feed_spec" in creative and "images" in creative["asset_feed_spec"]:
                    image_hashs.extend([image["hash"] for image in creative["asset_feed_spec"]["images"] if "hash" in image])

        # 4. if still no image hashes found, try to download directly from url
        if not image_hashs:

            if "data" in creatives_data and creatives_data["data"]:
                for creative in creatives_data["data"]:
                    # 4.1 image_urls_for_viewing, usually highest quality
                    if "image_urls_for_viewing" in creative and creative["image_urls_for_viewing"]:
                        image_url = creative["image_urls_for_viewing"][0]
                        break
                    # 4.2 image_url
                    elif "image_url" in creative and creative["image_url"]:
                        image_url = creative["image_url"]
                        break
                    # 4.3 object_story_spec
                    elif ("object_story_spec" in creative
                        and "link_data" in creative["object_story_spec"]
                        and "picture" in creative["object_story_spec"]["link_data"]):
                        image_url = creative["object_story_spec"]["link_data"]["picture"]
                        break
                    # 4.4 thumbnail_url
                    elif "thumbnail_url" in creative and creative["thumbnail_url"]:
                        image_url = creative["thumbnail_url"]
                        break

    # 5. found image hashs, download the first one
    if len(image_hashs) > 0:
        logger.info(f"Found image hashs: {image_hashs}")
        endpoint = f"{valid_account_id(account_id)}/adimages"
        params = {
            "fields": "hash,url,width,height,name,status",
            "hashes": f'["{image_hashs[0]}"]'
        }
        data = await make_api_request(endpoint, access_token, params)
        if "error" in data or "data" not in data or not data["data"]:
            return APIToolErrors.api_call_error(f"Failed to get ad image with hash {image_hashs[0]}", details=json.dumps(data, indent=2)).to_json()

        image_url = data["data"][0].get("url", "")

    # 6. Download image from url and process the image
    if not image_url:
        return APIToolErrors.api_call_error(f"No image URL found for ad {ad_id}")
    
    image_bytes = await _download_image(image_url)
    if not image_bytes:
        return APIToolErrors.api_call_error(f"Failed to download image from {image_url}")
    
    return json.dumps(
        {"type": "image", "base64": _convert2jpeg_base64(image_bytes), "mime_type": "image/jpeg"}, indent=2
    )


@tool
async def upload_ad_image(
    account_id: str,
    image_data: Optional[str] = None,
    image_url: Optional[str] = None,
    image_name: Optional[str] = None
) -> str:
    """
    Upload an image to a Meta Ads account from image data or image URL (one and only one is required).
    
    Args:
        account_id: Meta Ads account ID
        image_data: base64 encoded string of the image (e.g., {"type": "image", "base64": "...", "mime_type": "image/jpeg"})
        image_url: URL of the image to upload
        image_name: Name of the image
    """
    return await _upload_ad_image_kernel(account_id, image_data, image_url, image_name)


def upload_ad_image_tool(
    account_id: str,
    image_data: str | None = None,
    image_url: str | None = None,
    image_name: str | None = None
) -> str:
    """
    Upload an image to a Meta Ads account from image data or image URL (one and only one is required).
    If success, return the image hash.
    
    Args:
        account_id: Meta Ads account ID
        image_data: base64 encoded string of the image (e.g., {"type": "image", "base64": "...", "mime_type": "image/jpeg"})
        image_url: URL of the image to upload
        image_name: Name of the image
    """
    return asyncio.run(_upload_ad_image_kernel(account_id, image_data, image_url, image_name))


@meta_api_tool
async def _upload_ad_image_kernel(
    account_id: str,
    image_data: Optional[str] = None,
    image_url: Optional[str] = None,
    image_name: Optional[str] = None,
    access_token: Optional[str] = None,
) -> str:
    if not account_id:
        return APIToolErrors.no_account_id().to_json()
    
    if not image_data and not image_url:
        return APIToolErrors.arg_missing("image_data or image_url", "str", "Image data or image URL is required").to_json()

    image_base64 = None
    image_name = image_name or ""
    # 1. image data
    if image_data:
        try:
            image_data = json.loads(image_data)
            if "base64" not in image_data or not image_data["base64"]:
                return APIToolErrors.arg_invalid("image_data", "str", image_data, "Invalid image data").to_json()
            
            image_base64 = image_data["base64"].strip()
            if "mime_type" in image_data and image_data["mime_type"]:
                image_name = (image_name if image_name else "upload") + "." + image_data["mime_type"].split("/")[1]
            else:
                image_name = (image_name if image_name else "upload") + ".jpeg"

        except json.JSONDecodeError:
            return APIToolErrors.arg_invalid("image_data", "str", image_data, "Invalid image data").to_json()

    # 2. download image from url
    else:
        image_bytes = await _download_image(image_url)
        if not image_bytes:
            return APIToolErrors.api_call_error(f"Failed to download image from {image_url}").to_json()
        
        image_base64 = _convert2jpeg_base64(image_bytes)
        if not image_base64:
            return APIToolErrors.api_call_error(f"Failed to convert image to base64").to_json()
        
        if not image_name:
            try:
                image_name = os.path.basename(image_url.split("?")[0])
            except Exception:
                image_name = "upload.jpeg"
            image_name = image_name if image_name else "upload.jpeg"

    # 3. upload image
    endpoint = f"{valid_account_id(account_id)}/adimages"
    params = {
        "bytes": image_base64,
        "name": image_name,
    }

    logger.info(f"Uploading image to {endpoint} with params: {params}")
    data = await make_api_request(endpoint, access_token, params, method="POST")
    
    # Normalize/structure the response for callers (e.g., to easily grab image_hash)
    # Typical Graph API response shape:
    # { "images": { "<hash>": { "hash": "<hash>", "url": "...", "width": ..., "height": ..., "name": "...", "status": 1 } } }
    if isinstance(data, dict) and "images" in data and isinstance(data["images"], dict) and data["images"]:
        images_dict = data["images"]
        images_list = []
        for hash_key, info in images_dict.items():
            # Some responses may omit the nested hash, so ensure it's present
            normalized = {
                "hash": (info.get("hash") or hash_key),
                "url": info.get("url"),
                "width": info.get("width"),
                "height": info.get("height"),
                "name": info.get("name"),
            }
            # Drop null/None values
            normalized = {k: v for k, v in normalized.items() if v is not None}
            images_list.append(normalized)

        # Sort deterministically by hash
        images_list.sort(key=lambda i: i.get("hash", ""))
        primary_hash = images_list[0].get("hash") if images_list else None

        result = {
            "success": True,
            "account_id": account_id,
            "name": image_name,
            "image_hash": primary_hash,
            "images_count": len(images_list),
            "images": images_list
        }
        return json.dumps(result, indent=2)

    # If the API returned an error-like structure, surface it consistently
    if isinstance(data, dict) and "error" in data:
        return json.dumps({
            "error": "Failed to upload image",
            "details": data.get("error"),
            "account_id": account_id,
            "name": image_name
        }, indent=2)

    # Fallback: return a wrapped raw response to avoid breaking callers
    return json.dumps({
        "success": True,
        "account_id": account_id,
        "name": image_name,
        "raw_response": data
    }, indent=2)


# Internal helper functions
async def _download_image(image_url: str) -> Optional[bytes]:
    """
    Internal function to download an image from a URL.
    
    Args:
        image_url: URL of the image to download
    
    Returns:
        Optional[bytes]: The image bytes if successful, None if failed
    """
    try:
        logger.info(f"Downloading image from {image_url}")
        headers = {
            "User-Agent": "curl/8.4.0",
            "Accept": "*/*"
        }
        async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
            response = await client.get(image_url, headers=headers)

            if response.status_code == 200:
                logger.info(f"Image downloaded successfully from {image_url}")
                return response.content
            else:
                logger.error(f"Failed to download image from {image_url}: {response.status_code}")
                return None
    except httpx.HTTPError as e:
        logger.error(f"HTTP error downloading image: {e}")
        return None
    except Exception as e:
        logger.error(f"Error downloading image: {e}")
        return None


def _convert2jpeg_base64(image_bytes: bytes) -> str:
    """
    Internal function to convert an image to a base64 encoded string of the image.
    """
    image = Image.open(io.BytesIO(image_bytes))
    if image.mode != "RGB":
        image = image.convert("RGB")
    byte_buf = io.BytesIO()
    image.save(byte_buf, format="JPEG")
    return base64.b64encode(byte_buf.getvalue()).decode("utf-8")

