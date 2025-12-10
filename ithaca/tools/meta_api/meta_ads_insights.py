"""
Meta Ads Insights Tools.
Provides a single, consistent interface to retrieve an ad's statistics. 
The Ad Insights API can return several metrics which are estimated or in-development. 
In some cases a metric may be both estimated and in-development.
Cite from: https://developers.facebook.com/docs/marketing-api/reference/adgroup/insights

- get_insights: Get performance insights for a Meta Ads 'campaign', 'ad set', 'ad' or 'account'.
"""
from typing import Optional, Dict, Any, Union
import json
import re
from datetime import datetime, timedelta
import asyncio

from ithaca.tools.meta_api.meta_ads_api import make_api_request, meta_api_tool
from ithaca.tools.meta_api.utils import concise_return_message, APIToolErrors


def get_campaign_insights_tool(
    campaign_id: str,
    days_ago: int = 1,
    after: str = "",
    limit: int = 25,
):
    """
    Get performance insights for a Meta Ads campaign.
    The query fields are: "account_id,account_name,campaign_id,campaign_name,adset_id,adset_name,ad_id,ad_name,impressions,clicks,spend,cpc,cpm,ctr,reach,frequency,actions,action_values,conversions,unique_clicks,cost_per_action_type"

    Args:
        campaign_id: The ID of the campaign.
        days_ago: The number of days ago until now to get the insights. Default is 1 day ago. 1 <= days_ago <= 30 * 30.
        after: Pagination cursor to get the next set of results. Use the 'after' cursor from previous response's paging.next field.
        limit: Maximum number of results to return per page (default: 25, Meta API allows much higher values)
    """
    if days_ago < 1 or days_ago > 30 * 30:
        return APIToolErrors.error(message=f"Invalid days_ago: {days_ago}. 1 <= days_ago <= 30 * 30.", example="days_ago=1").to_json()
    time_range = {"since":(datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d"),"until":datetime.now().strftime("%Y-%m-%d")}
    return asyncio.run(get_insights_kernel(id=campaign_id, time_range=time_range, level="campaign", after=after, limit=limit))


def get_adset_insights_tool(
    adset_id: str,
    days_ago: int = 1,
    after: str = "",
    limit: int = 25,
):
    """
    Get performance insights for a Meta Ads adset.
    The query fields are: "account_id,account_name,campaign_id,campaign_name,adset_id,adset_name,ad_id,ad_name,impressions,clicks,spend,cpc,cpm,ctr,reach,frequency,actions,action_values,conversions,unique_clicks,cost_per_action_type"

    Args:
        adset_id: The ID of the adset.
        days_ago: The number of days ago until now to get the insights. Default is 1 day ago. 1 <= days_ago <= 30 * 30.
        after: Pagination cursor to get the next set of results. Use the 'after' cursor from previous response's paging.next field.
        limit: Maximum number of results to return per page (default: 25, Meta API allows much higher values)
    """
    if days_ago < 1 or days_ago > 30 * 30:
        return APIToolErrors.error(message=f"Invalid days_ago: {days_ago}. 1 <= days_ago <= 30 * 30.", example="days_ago=1").to_json()
    time_range = {"since":(datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d"),"until":datetime.now().strftime("%Y-%m-%d")}
    return asyncio.run(get_insights_kernel(id=adset_id, time_range=time_range, level="adset", after=after, limit=limit))


def get_ad_insights_tool(
    ad_id: str,
    days_ago: int = 1,
    after: str = "",
    limit: int = 25,
):
    """
    Get performance insights for a Meta Ads ad.
    The query fields are: "account_id,account_name,campaign_id,campaign_name,adset_id,adset_name,ad_id,ad_name,impressions,clicks,spend,cpc,cpm,ctr,reach,frequency,actions,action_values,conversions,unique_clicks,cost_per_action_type"

    Args:
        ad_id: The ID of the ad.
        days_ago: The number of days ago until now to get the insights. Default is 1 day ago. 1 <= days_ago <= 30 * 30.
        after: Pagination cursor to get the next set of results. Use the 'after' cursor from previous response's paging.next field.
        limit: Maximum number of results to return per page (default: 25, Meta API allows much higher values)
    """
    if days_ago < 1 or days_ago > 30 * 30:  
        return APIToolErrors.error(message=f"Invalid days_ago: {days_ago}. 1 <= days_ago <= 30 * 30.", example="days_ago=1").to_json()
    time_range = {"since":(datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d"),"until":datetime.now().strftime("%Y-%m-%d")}
    return asyncio.run(get_insights_kernel(id=ad_id, time_range=time_range, level="ad", after=after, limit=limit))


TIME_RANGE_PRESETS = [
    'today', 'yesterday', 'this_month', 'last_month', 'this_quarter', 'maximum', 'data_maximum', 
    'last_3d', 'last_7d', 'last_14d', 'last_28d', 'last_30d', 'last_90d', 'last_week_mon_sun', 
    'last_week_sun_sat', 'last_quarter', 'last_year', 'this_week_mon_today', 'this_week_sun_today', 'this_year'
]

#TODO: This is an aggregated tool for now, 
#TODO: we need to separate this for detailed insights.
def get_insights_tool(
    id: str,
    time_range: Union[str, Dict[str, str]] = {"since":(datetime.now() - timedelta(days=30 * 30)).strftime("%Y-%m-%d"),"until":datetime.now().strftime("%Y-%m-%d")},
    breakdown: str = "",
    level: str = "ad",
    after: str = "",
    limit: int = 25,
):
    """
    Get performance insights for a Meta Ads 'campaign', 'ad set', 'ad' or 'account'.
    The query fields are: "account_id,account_name,campaign_id,campaign_name,adset_id,adset_name,ad_id,ad_name,impressions,clicks,spend,cpc,cpm,ctr,reach,frequency,actions,action_values,conversions,unique_clicks,cost_per_action_type"

    Args:
        id: The ID of the 'campaign', 'ad set', 'ad' or 'account'.
        time_range: Either a preset time range string or a dictionary with "since" and "until" dates in YYYY-MM-DD format
                   Preset options: today, yesterday, this_month, last_month, this_quarter, maximum, data_maximum, 
                   last_3d, last_7d, last_14d, last_28d, last_30d, last_90d, last_week_mon_sun, 
                   last_week_sun_sat, last_quarter, last_year, this_week_mon_today, this_week_sun_today, this_year
                   Dictionary example: {"since":"2023-01-01","until":"2023-01-31"}
        breakdown: Optional breakdown dimension. Valid values include:
                   Demographic: age, gender, country, region, dma
                   Platform/Device: device_platform, platform_position, publisher_platform, impression_device
                   Creative Assets: ad_format_asset, body_asset, call_to_action_asset, description_asset, 
                                  image_asset, link_url_asset, title_asset, video_asset, media_asset_url,
                                  media_creator, media_destination_url, media_format, media_origin_url,
                                  media_text_content, media_type, creative_relaxation_asset_type,
                                  flexible_format_asset_type, gen_ai_asset_type
                   Campaign/Ad Attributes: breakdown_ad_objective, breakdown_reporting_ad_id, app_id, product_id
                   Conversion Tracking: coarse_conversion_value, conversion_destination, standard_event_content_type,
                                       signal_source_bucket, is_conversion_id_modeled, fidelity_type, redownload
                   Time-based: hourly_stats_aggregated_by_advertiser_time_zone, 
                              hourly_stats_aggregated_by_audience_time_zone, frequency_value
                   Extensions/Landing: ad_extension_domain, ad_extension_url, landing_destination, 
                                      mdsa_landing_destination
                   Attribution: sot_attribution_model_type, sot_attribution_window, sot_channel, 
                               sot_event_type, sot_source
                   Mobile/SKAN: skan_campaign_id, skan_conversion_id, skan_version, postback_sequence_index
                   CRM/Business: crm_advertiser_l12_territory_ids, crm_advertiser_subvertical_id,
                                crm_advertiser_vertical_id, crm_ult_advertiser_id, user_persona_id, user_persona_name
                   Advanced: hsid, is_auto_advance, is_rendered_as_delayed_skip_ad, mmm, place_page_id,
                            marketing_messages_btn_name, impression_view_time_advertiser_hour_v2, comscore_market,
                            comscore_market_code
        level: Level of aggregation (ad, adset, campaign, account)
        limit: Maximum number of results to return per page (default: 25, Meta API allows much higher values)
        after: Pagination cursor to get the next set of results. Use the 'after' cursor from previous response's paging.next field.
    """
    return asyncio.run(get_insights_kernel(id, time_range, breakdown, level, after, limit))


@meta_api_tool
async def get_insights_kernel(
    id: str,
    time_range: Union[str, Dict[str, str]] = {"since":(datetime.now() - timedelta(days=30 * 30)).strftime("%Y-%m-%d"),"until":datetime.now().strftime("%Y-%m-%d")},
    breakdown: str = "",
    level: str = "ad",
    after: str = "",
    limit: int = 25,
    access_token: Optional[str] = None,
) -> str:
    """
    Get performance insights for a Meta Ads 'campaign', 'ad set', 'ad' or 'account'.
    The query fields are: "account_id,account_name,campaign_id,campaign_name,adset_id,adset_name,ad_id,ad_name,impressions,clicks,spend,cpc,cpm,ctr,reach,frequency,actions,action_values,conversions,unique_clicks,cost_per_action_type"

    Args:
        id: The ID of the 'campaign', 'ad set', 'ad' or 'account'.
        time_range: Either a preset time range string or a dictionary with "since" and "until" dates in YYYY-MM-DD format
                   Preset options: today, yesterday, this_month, last_month, this_quarter, maximum, data_maximum, 
                   last_3d, last_7d, last_14d, last_28d, last_30d, last_90d, last_week_mon_sun, 
                   last_week_sun_sat, last_quarter, last_year, this_week_mon_today, this_week_sun_today, this_year
                   Dictionary example: {"since":"2023-01-01","until":"2023-01-31"}
        breakdown: Optional breakdown dimension. Valid values include:
                   Demographic: age, gender, country, region, dma
                   Platform/Device: device_platform, platform_position, publisher_platform, impression_device
                   Creative Assets: ad_format_asset, body_asset, call_to_action_asset, description_asset, 
                                  image_asset, link_url_asset, title_asset, video_asset, media_asset_url,
                                  media_creator, media_destination_url, media_format, media_origin_url,
                                  media_text_content, media_type, creative_relaxation_asset_type,
                                  flexible_format_asset_type, gen_ai_asset_type
                   Campaign/Ad Attributes: breakdown_ad_objective, breakdown_reporting_ad_id, app_id, product_id
                   Conversion Tracking: coarse_conversion_value, conversion_destination, standard_event_content_type,
                                       signal_source_bucket, is_conversion_id_modeled, fidelity_type, redownload
                   Time-based: hourly_stats_aggregated_by_advertiser_time_zone, 
                              hourly_stats_aggregated_by_audience_time_zone, frequency_value
                   Extensions/Landing: ad_extension_domain, ad_extension_url, landing_destination, 
                                      mdsa_landing_destination
                   Attribution: sot_attribution_model_type, sot_attribution_window, sot_channel, 
                               sot_event_type, sot_source
                   Mobile/SKAN: skan_campaign_id, skan_conversion_id, skan_version, postback_sequence_index
                   CRM/Business: crm_advertiser_l12_territory_ids, crm_advertiser_subvertical_id,
                                crm_advertiser_vertical_id, crm_ult_advertiser_id, user_persona_id, user_persona_name
                   Advanced: hsid, is_auto_advance, is_rendered_as_delayed_skip_ad, mmm, place_page_id,
                            marketing_messages_btn_name, impression_view_time_advertiser_hour_v2, comscore_market,
                            comscore_market_code
        level: Level of aggregation (ad, adset, campaign, account)
        limit: Maximum number of results to return per page (default: 25, Meta API allows much higher values)
        after: Pagination cursor to get the next set of results. Use the 'after' cursor from previous response's paging.next field.
        access_token: Meta API access token (optional - will use cached token if not provided)
    """
    if not id:
        return APIToolErrors.no_id().to_json()
    
    endpoint = f"{id}/insights"
    params = {
        "fields": "account_id,account_name,campaign_id,campaign_name,adset_id,adset_name,ad_id,ad_name,impressions,clicks,spend,cpc,cpm,ctr,reach,frequency,actions,action_values,conversions,unique_clicks,cost_per_action_type",
        "level": level,
        "limit": limit
    }

    if isinstance(time_range, dict):
        pattern = r"^\d{4}-\d{2}-\d{2}$"
        if ("since" in time_range and "until" in time_range and 
            re.match(pattern, time_range["since"]) and re.match(pattern, time_range["until"])):
            params["time_range"] = json.dumps(time_range)
        else:
            return APIToolErrors.invalid_time_range(time_range).to_json()
    else:
        if time_range in TIME_RANGE_PRESETS:
            params["time_range"] = time_range
        else:
            return APIToolErrors.invalid_time_range(time_range).to_json()
    
    if breakdown:
        params["breakdown"] = breakdown
    
    if after:
        params["after"] = after
    
    data = await make_api_request(endpoint, access_token, params)
    return concise_return_message(data, params=params)


