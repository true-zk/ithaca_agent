"""
Utility functions for Meta Ads API.
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any, List, Union
import json


# For tool error
@dataclass
class ToolError:
    """Error template for API tools."""
    message: str
    details: Optional[str] = None
    example: Optional[str] = None
    suggestions: Optional[str] = None
    params_sent: Optional[Dict[str, Any]] = None
    extra_fields: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        data = {
            "error": {
                "message": self.message,
            }
        }
        for key, value in self.__dict__.items():
            if value is not None and key != "params_sent" and key != "extra_fields":
                data["error"][key] = value
        if self.params_sent is not None:
            data["params_sent"] = self.params_sent
        if self.extra_fields is not None:
            for key, value in self.extra_fields.items():
                data[key] = value
        return data
    
    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)


class APIToolErrors:
    """API tool error factory class."""

    @staticmethod
    def error(
        message: str, 
        details: Optional[str] = None, 
        example: Optional[str] = None, 
        suggestions: Optional[str] = None, 
        params_sent: Optional[Dict[str, Any]] = None,
        extra_fields: Optional[Dict[str, Any]] = None
    ) -> ToolError:
        """Create a ToolError instance."""
        return ToolError(
            message=message,
            details=details,
            example=example,
            suggestions=suggestions,
            params_sent=params_sent,
            extra_fields=extra_fields,
        )

    @staticmethod
    def api_call_error(
        message: str,
        details: Optional[str] = None,
        params_sent: Optional[Dict[str, Any]] = None,
    ) -> ToolError:
        return ToolError(
            message=message,
            details=details,
            params_sent=params_sent,
        )
    
    @staticmethod
    def no_account_id() -> ToolError:
        return ToolError(
            message="Account ID is required",
            details="Account ID parameter cannot be empty or None",
            example="Use account_id='act_1234567890' or account_id='1234567890'"
        )
    
    @staticmethod
    def account_not_accessible(account_id: str, accessible_accounts: List[Dict[str, Any]]) -> ToolError:
        accessible_accounts_str = json.dumps(accessible_accounts, indent=2)
        return ToolError(
            message=f"Account ID {account_id} is not accessible",
            details=f"You don't have permission to access this account. {accessible_accounts_str}",
            suggestions="Try using one of the accessible accounts listed in the details"
        )

    @staticmethod
    def no_id() -> ToolError:
        return ToolError(
            message="ID is required",
            details="Should provide a valid 'campaign', 'ad set', 'ad' or 'account' ID",
        )

    @staticmethod
    def invalid_time_range(time_range: Dict[str, str]) -> ToolError:
        return ToolError(
            message="Invalid time range argument",
            details=f"Time range should be a dictionary with 'since' and 'until' keys in YYYY-MM-DD format. Got: {time_range}",
            example='{"since":"2023-01-01","until":"2023-01-31"}',
        )
    
    @staticmethod
    def no_campaign_id() -> ToolError:
        return ToolError(
            message="Campaign ID is required",
            details="Campaign ID parameter cannot be empty or None",
            example="Use campaign_id='1234567890' or campaign_id='1234567890'"
        )
    
    @staticmethod
    def arg_missing(arg_name: str, arg_type: str, details: str, example: str = None) -> ToolError:
        return ToolError(
            message=f"Argument {arg_name} with type {arg_type} is required",
            details=details,
            example=example,
        )
    
    @staticmethod
    def arg_invalid(arg_name: str, arg_type: str, value: Any, details: str, example: str = None) -> ToolError:
        return ToolError(
            message=f"Argument {arg_name} with type {arg_type}, invalid value: {value}",
            details=details,
            example=example,
        )
    
    @staticmethod
    def invalid_enum_value(arg_name: str, valid_values: List[str], value: str) -> ToolError:
        return ToolError(
            message=f"Enum argument {arg_name} with value '{value}' is invalid",
            details=f"Valid values for {arg_name} are: {valid_values}",
        )


# For api params
class EnumArgValidator:
    """Enum argument validator class."""
    def __init__(self, arg_name: str, valid_values: Union[str, List[str]]):
        self._arg_name = arg_name
        if isinstance(valid_values, str):
            valid_values = valid_values.split(",")
            valid_values = [val.strip().replace("'", "").replace('"', "").upper() for val in valid_values]
        self.valid_values = valid_values
    
    @property
    def arg_name(self) -> str:
        return self._arg_name
    
    def validate(self, value: str) -> bool:
        """Validate if the value is in the valid values."""
        return value.upper() in self.valid_values
    
    def error(self, value: str) -> ToolError:
        return APIToolErrors.invalid_enum_value(self._arg_name, self.valid_values, value)


EFFECTIVE_STATUS_VALIDATOR = EnumArgValidator("effective_status", ["", "ACTIVE", "PAUSED", "ARCHIVED", "DELETED", "IN_PROCESS", "WITH_ISSUES"])
STATUS_VALIDATOR = EnumArgValidator("status", ["ACTIVE", "PAUSED", "ARCHIVED", "DELETED"])
OBJECTIVE_VALIDATOR = EnumArgValidator("objective", ["OUTCOME_AWARENESS", "OUTCOME_TRAFFIC", "OUTCOME_ENGAGEMENT", "OUTCOME_LEADS", "OUTCOME_SALES", "OUTCOME_APP_PROMOTION"])
BID_STRATEGY_VALIDATOR = EnumArgValidator("bid_strategy", ["LOWEST_COST_WITHOUT_CAP", "LOWEST_COST_WITH_BID_CAP", "COST_CAP", "LOWEST_COST_WITH_MIN_ROAS"])
OPTIMIZATION_GOAL_VALIDATOR = EnumArgValidator("optimization_goal", ["NONE", "APP_INSTALLS", "AD_RECALL_LIFT", "ENGAGED_USERS", "EVENT_RESPONSES", "IMPRESSIONS", "LEAD_GENERATION", "QUALITY_LEAD", "LINK_CLICKS", "OFFSITE_CONVERSIONS", "PAGE_LIKES", "POST_ENGAGEMENT", "QUALITY_CALL", "REACH", "LANDING_PAGE_VIEWS", "VISIT_INSTAGRAM_PROFILE", "VALUE", "THRUPLAY", "DERIVED_EVENTS", "APP_INSTALLS_AND_OFFSITE_CONVERSIONS", "CONVERSATIONS", "IN_APP_VALUE", "MESSAGING_PURCHASE_CONVERSION", "SUBSCRIBERS", "REMINDERS_SET", "MEANINGFUL_CALL_ATTEMPT", "PROFILE_VISIT", "PROFILE_AND_PAGE_ENGAGEMENT", "ADVERTISER_SILOED_VALUE", "AUTOMATIC_OBJECTIVE", "MESSAGING_APPOINTMENT_CONVERSION"])
BILLING_EVENT_VALIDATOR = EnumArgValidator("billing_event", ["APP_INSTALLS", "CLICKS", "IMPRESSIONS", "LINK_CLICKS", "NONE", "OFFER_CLAIMS", "PAGE_LIKES", "POST_ENGAGEMENT", "THRUPLAY", "PURCHASE", "LISTING_INTERACTION"])
DESTINATION_TYPE_VALIDATOR = EnumArgValidator("destination_type", ["WEBSITE", "APP", "MESSENGER", "APPLINKS_AUTOMATIC", "WHATSAPP", "INSTAGRAM_DIRECT", "FACEBOOK", "MESSAGING_MESSENGER_WHATSAPP", "MESSAGING_INSTAGRAM_DIRECT_MESSENGER", "MESSAGING_INSTAGRAM_DIRECT_MESSENGER_WHATSAPP", "MESSAGING_INSTAGRAM_DIRECT_WHATSAPP", "SHOP_AUTOMATIC", "ON_AD", "ON_POST", "ON_EVENT", "ON_VIDEO", "ON_PAGE", "INSTAGRAM_PROFILE", "FACEBOOK_PAGE", "INSTAGRAM_PROFILE_AND_FACEBOOK_PAGE", "INSTAGRAM_LIVE", "FACEBOOK_LIVE", "IMAGINE"])
DELETE_STRATEGY_VALIDATOR = EnumArgValidator("delete_strategy", ["DELETE_ANY", "DELETE_OLDEST", "DELETE_ARCHIVED_BEFORE"])


enum_arg_validators = {
    "effective_status": EFFECTIVE_STATUS_VALIDATOR,
    "status": STATUS_VALIDATOR,
    "objective": OBJECTIVE_VALIDATOR,
    "bid_strategy": BID_STRATEGY_VALIDATOR,
    "optimization_goal": OPTIMIZATION_GOAL_VALIDATOR,
    "billing_event": BILLING_EVENT_VALIDATOR,
    "destination_type": DESTINATION_TYPE_VALIDATOR,
    "delete_strategy": DELETE_STRATEGY_VALIDATOR,
}


def valid_account_id(account_id: str) -> str:
    if not account_id.startswith("act_"):
        account_id = f"act_{account_id}"
    return account_id


def concise_return_message(data, params: Optional[Dict] = None) -> str:
    """Convert the data to a concise return message."""
    if "error" in data:
        error = data["error"]["details"]["error"]
        if params:
            params.pop("access_token", None)
        if error.get("error_user_title"):
            error_msg = {
                "type": data["error"]["message"],
                "title": error["error_user_title"],
                "message": error["error_user_msg"],
                "params_sent": params,
            }
        else:
            error_msg = {
                "type": data["error"]["message"],
                "message": error["message"],
                "params_sent": params,
            }
        return json.dumps(error_msg, indent=2)
    return json.dumps(data, indent=2)