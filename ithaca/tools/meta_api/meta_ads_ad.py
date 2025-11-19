"""
Meta Ads ad Tools.
Cite from: https://developers.facebook.com/docs/marketing-api/reference/adgroup


"""
from typing import Optional, Dict, Any
import json

from langchain.tools import tool

from ithaca.tools.meta_api.meta_ads_api import make_api_request, meta_api_tool


@tool
@meta_api_tool
async def get_ads(
    
)