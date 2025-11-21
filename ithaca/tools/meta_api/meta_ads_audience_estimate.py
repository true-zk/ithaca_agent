"""
Meta Ads Targeting and Audience Estimation Tools.
"""
from typing import Optional, Dict, Any, List
import json
import os

from langchain.tools import tool

from ithaca.logger import logger
from ithaca.tools.meta_api.meta_ads_api import make_api_request, meta_api_tool
from ithaca.tools.meta_api.utils import APIToolErrors, valid_account_id


class TargetingValidator:
    """目标受众定位验证器"""
    
    @staticmethod
    def validate_targeting_spec(targeting: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证目标受众定位规范
        
        Args:
            targeting: 目标受众定位字典
            
        Returns:
            验证结果
        """
        if not isinstance(targeting, dict):
            return {
                "valid": False,
                "error": "Targeting must be a dictionary"
            }
        
        # 检查是否有地理位置或自定义受众
        has_location = TargetingValidator._has_geo_location(targeting)
        has_custom_audience = TargetingValidator._has_custom_audience(targeting)
        
        if not has_location and not has_custom_audience:
            return {
                "valid": False,
                "error": {
                    "message": "Missing target audience location",
                    "details": "Must include geo_locations or custom_audiences",
                    "example": {
                        "geo_locations": {"countries": ["US"]},
                        "age_min": 25,
                        "age_max": 65
                    }
                }
            }
        
        return {"valid": True}
    
    @staticmethod
    def _has_geo_location(targeting: Dict[str, Any]) -> bool:
        """检查是否有地理位置定位"""
        geo_locations = targeting.get("geo_locations", {})
        if not isinstance(geo_locations, dict):
            return False
        
        location_keys = ["countries", "regions", "cities", "zips", "geo_markets", "country_groups"]
        return any(
            isinstance(geo_locations.get(key), list) and len(geo_locations[key]) > 0
            for key in location_keys
        )
    
    @staticmethod
    def _has_custom_audience(targeting: Dict[str, Any]) -> bool:
        """检查是否有自定义受众"""
        # 顶级自定义受众
        custom_audiences = targeting.get("custom_audiences", [])
        if isinstance(custom_audiences, list) and len(custom_audiences) > 0:
            return True
        
        # flexible_spec 中的自定义受众
        flexible_spec = targeting.get("flexible_spec", [])
        if isinstance(flexible_spec, list):
            for spec in flexible_spec:
                if isinstance(spec, dict):
                    spec_audiences = spec.get("custom_audiences", [])
                    if isinstance(spec_audiences, list) and len(spec_audiences) > 0:
                        return True
        
        return False


class AudienceEstimator:
    """受众规模估算器"""
    
    def __init__(self):
        self.fallback_enabled = os.environ.get("META_AUDIENCE_FALLBACK_ENABLED", "true").lower() == "true"
    
    async def estimate_reach(
        self, 
        account_id: str, 
        targeting: Dict[str, Any], 
        access_token: str,
        optimization_goal: str = "REACH"
    ) -> Dict[str, Any]:
        """
        估算受众规模
        
        Args:
            account_id: 广告账户ID
            targeting: 目标受众定位
            access_token: 访问令牌
            optimization_goal: 优化目标
            
        Returns:
            估算结果
        """
        # 验证定位规范
        validation = TargetingValidator.validate_targeting_spec(targeting)
        if not validation["valid"]:
            return validation
        
        # 尝试主要 API
        try:
            result = await self._call_reach_estimate_api(account_id, targeting, access_token)
            if result.get("success"):
                return result
            
            # 如果主要 API 失败且启用了回退，尝试回退
            if self.fallback_enabled:
                logger.warning(f"Reach estimate failed, trying fallback: {result.get('error')}")
                return await self._call_delivery_estimate_fallback(account_id, targeting, access_token, optimization_goal)
            
            return result
            
        except Exception as e:
            logger.error(f"Audience estimation failed: {str(e)}")
            
            if self.fallback_enabled:
                try:
                    return await self._call_delivery_estimate_fallback(account_id, targeting, access_token, optimization_goal)
                except Exception as fallback_error:
                    logger.error(f"Fallback also failed: {str(fallback_error)}")
            
            return {
                "success": False,
                "error": {
                    "message": "Audience estimation failed",
                    "details": str(e),
                    "endpoint_used": f"{account_id}/reachestimate"
                }
            }
    
    async def _call_reach_estimate_api(
        self, 
        account_id: str, 
        targeting: Dict[str, Any], 
        access_token: str
    ) -> Dict[str, Any]:
        """调用 reach estimate API"""
        endpoint = f"{account_id}/reachestimate"
        params = {"targeting_spec": targeting}
        
        data = await make_api_request(endpoint, access_token, params, method="GET")
        
        if "error" in data:
            return {
                "success": False,
                "error": data["error"],
                "endpoint_used": endpoint
            }
        
        return self._format_reach_estimate_response(data, account_id, targeting)
    
    async def _call_delivery_estimate_fallback(
        self, 
        account_id: str, 
        targeting: Dict[str, Any], 
        access_token: str,
        optimization_goal: str
    ) -> Dict[str, Any]:
        """回退到 delivery estimate API"""
        endpoint = f"{account_id}/delivery_estimate"
        params = {
            "targeting_spec": json.dumps(targeting),
            "optimization_goal": optimization_goal
        }
        
        data = await make_api_request(endpoint, access_token, params, method="GET")
        
        if "error" in data:
            return {
                "success": False,
                "error": data["error"],
                "endpoint_used": endpoint,
                "is_fallback": True
            }
        
        return self._format_delivery_estimate_response(data, account_id, targeting, optimization_goal)
    
    def _format_reach_estimate_response(
        self, 
        data: Dict[str, Any], 
        account_id: str, 
        targeting: Dict[str, Any]
    ) -> Dict[str, Any]:
        """格式化 reach estimate 响应"""
        if "data" not in data:
            return {
                "success": False,
                "error": {
                    "message": "No data in API response",
                    "raw_response": data
                }
            }
        
        response_data = data["data"]
        
        # 处理字典格式响应（reachestimate）
        if isinstance(response_data, dict):
            lower = response_data.get("users_lower_bound", 0)
            upper = response_data.get("users_upper_bound", 0)
            estimate_ready = response_data.get("estimate_ready", False)
            
            midpoint = int((lower + upper) / 2) if lower and upper else 0
            
            return {
                "success": True,
                "account_id": account_id,
                "targeting": targeting,
                "estimated_audience_size": midpoint,
                "estimate_details": {
                    "users_lower_bound": lower,
                    "users_upper_bound": upper,
                    "estimate_ready": estimate_ready
                },
                "endpoint_used": "reachestimate"
            }
        
        return {
            "success": False,
            "error": {
                "message": "Unexpected response format",
                "raw_response": data
            }
        }
    
    def _format_delivery_estimate_response(
        self, 
        data: Dict[str, Any], 
        account_id: str, 
        targeting: Dict[str, Any],
        optimization_goal: str
    ) -> Dict[str, Any]:
        """格式化 delivery estimate 响应"""
        if "data" not in data or not isinstance(data["data"], list) or len(data["data"]) == 0:
            return {
                "success": False,
                "error": {
                    "message": "No estimation data returned",
                    "raw_response": data
                }
            }
        
        estimate_data = data["data"][0]
        
        return {
            "success": True,
            "account_id": account_id,
            "targeting": targeting,
            "optimization_goal": optimization_goal,
            "estimated_audience_size": estimate_data.get("estimate_mau", 0),
            "estimate_details": {
                "monthly_active_users": estimate_data.get("estimate_mau", 0),
                "daily_outcomes_curve": estimate_data.get("estimate_dau", []),
                "bid_estimate": estimate_data.get("bid_estimates", {}),
                "unsupported_targeting": estimate_data.get("unsupported_targeting", [])
            },
            "endpoint_used": "delivery_estimate",
            "is_fallback": True
        }


class InterestValidator:
    """兴趣验证器（向后兼容）"""
    
    @staticmethod
    async def validate_interests(
        interest_list: Optional[List[str]] = None,
        interest_fbid_list: Optional[List[str]] = None,
        access_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        验证兴趣列表
        
        Args:
            interest_list: 兴趣名称列表
            interest_fbid_list: 兴趣ID列表
            access_token: 访问令牌
            
        Returns:
            验证结果
        """
        if not interest_list and not interest_fbid_list:
            return {
                "success": False,
                "error": {
                    "message": "No interests provided",
                    "details": "Must provide either interest_list or interest_fbid_list"
                }
            }
        
        endpoint = "search"
        params = {"type": "adinterestvalid"}
        
        if interest_list:
            params["interest_list"] = json.dumps(interest_list)
        
        if interest_fbid_list:
            params["interest_fbid_list"] = json.dumps(interest_fbid_list)
        
        try:
            data = await make_api_request(endpoint, access_token, params)
            return {
                "success": True,
                "validation_results": data,
                "endpoint_used": "search (adinterestvalid)"
            }
        except Exception as e:
            return {
                "success": False,
                "error": {
                    "message": "Interest validation failed",
                    "details": str(e)
                }
            }


@tool
@meta_api_tool
async def estimate_audience_size(
    access_token: Optional[str] = None,
    account_id: Optional[str] = None,
    targeting: Optional[Dict[str, Any]] = None,
    optimization_goal: str = "REACH",
    # 向后兼容参数
    interest_list: Optional[List[str]] = None,
    interest_fbid_list: Optional[List[str]] = None
) -> str:
    """
    Estimate audience size for targeting specifications using Meta's API.
    
    This function provides audience estimation for targeting combinations and maintains
    backwards compatibility for simple interest validation.
    
    Args:
        access_token: Meta API access token (optional - will use cached token if not provided)
        account_id: Meta Ads account ID (format: act_XXXXXXXXX) - required for comprehensive estimation
        targeting: Complete targeting specification including demographics, geography, interests, etc.
                  Example: {
                      "age_min": 25,
                      "age_max": 65,
                      "geo_locations": {"countries": ["US"]},
                      "flexible_spec": [
                          {"interests": [{"id": "6003371567474"}]}
                      ]
                  }
        optimization_goal: Optimization goal for estimation (default: "REACH")
        interest_list: [DEPRECATED] List of interest names to validate
        interest_fbid_list: [DEPRECATED] List of interest IDs to validate
    
    Returns:
        JSON string with audience estimation results
    """
    
    # 向后兼容：简单兴趣验证
    is_legacy_call = (interest_list or interest_fbid_list) or (not account_id and not targeting)
    
    if is_legacy_call and not targeting:
        logger.info("Using legacy interest validation mode")
        result = await InterestValidator.validate_interests(
            interest_list=interest_list,
            interest_fbid_list=interest_fbid_list,
            access_token=access_token
        )
        return json.dumps(result, indent=2)
    
    # 综合受众估算
    if not account_id:
        return json.dumps({
            "error": {
                "message": "Account ID required",
                "details": "account_id is required for comprehensive audience estimation",
                "example": "act_1234567890"
            }
        }, indent=2)
    
    if not targeting:
        return json.dumps({
            "error": {
                "message": "Targeting specification required",
                "details": "targeting parameter is required for audience estimation",
                "example": {
                    "age_min": 25,
                    "age_max": 65,
                    "geo_locations": {"countries": ["US"]},
                    "flexible_spec": [
                        {"interests": [{"id": "6003371567474"}]}
                    ]
                }
            }
        }, indent=2)
    
    # 格式化账户ID
    account_id = valid_account_id(account_id)
    
    # 执行受众估算
    estimator = AudienceEstimator()
    result = await estimator.estimate_reach(
        account_id=account_id,
        targeting=targeting,
        access_token=access_token,
        optimization_goal=optimization_goal
    )
    
    return json.dumps(result, indent=2)


# 辅助工具函数
@tool
@meta_api_tool
async def validate_targeting_interests(
    interest_list: List[str],
    access_token: Optional[str] = None
) -> str:
    """
    Validate a list of interest names for targeting.
    
    Args:
        interest_list: List of interest names to validate
        access_token: Meta API access token (optional)
    
    Returns:
        JSON string with validation results
    """
    result = await InterestValidator.validate_interests(
        interest_list=interest_list,
        access_token=access_token
    )
    return json.dumps(result, indent=2)


@tool
@meta_api_tool
async def validate_targeting_interest_ids(
    interest_fbid_list: List[str],
    access_token: Optional[str] = None
) -> str:
    """
    Validate a list of interest IDs for targeting.
    
    Args:
        interest_fbid_list: List of interest Facebook IDs to validate
        access_token: Meta API access token (optional)
    
    Returns:
        JSON string with validation results
    """
    result = await InterestValidator.validate_interests(
        interest_fbid_list=interest_fbid_list,
        access_token=access_token
    )
    return json.dumps(result, indent=2)