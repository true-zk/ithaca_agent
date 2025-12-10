"""
Data type for Meta Ads workflow.

Campaigns -> Adsets -| 
                     |
Images -> Creatives --> Ads 

- E.g., creating an Adset will ask a Campaign_id.
    And the Adset should obey the constrains of the Campaign.
    E.g., A Campaign with `objective = OUTCOME_APP_PROMOTION` asks
    its Adsets containing specific `promoted_object`.
- The constrains have chain effect: from Campaign to even Creatives.
- Creatives are attached to a Meta Page
"""
from ast import Str
from typing import Optional, List, Dict, Any, Union
from enum import Enum
import json
from pydantic import BaseModel, Field


class WorkflowStatus(Enum):
    INITIALIZED = "initialized"
    EXECUTING = "executing"
    COMPLETED = "completed"  # ready to finish
    FINISHED = "finished"


class MarketingPlanStatus(Enum):
    """
    Status of a marketing plan, according to the `STATUS` of campaign.

    - INITIALIZED
    - ACTIVE
    - PAUSED
    - DELETED
    """
    INITIALIZED = "initialized"
    ACTIVE = "active"
    PAUSED = "paused"
    DELETED = "deleted"


# Workflow data type
class MarketingInitInput(BaseModel):
    """
    The initial input of a marketing plan.
    """
    product_name: str
    product_url: str
    total_budget: Optional[float] = None
    total_days: Optional[int] = None
    product_picture_urls: Optional[List[str]] = Field(default_factory=list)

    def to_str(self) -> str:
        init_input_str = """The initial input of a marketing plan:
Product Name: {product_name},
Product Url: {product_url},
Optional Total Budget: {total_budget},
Optional Total Days for the marketing plan to execute: {total_days}
Optional Picture Urls of the product for creating Meta Ads Creatives: 
{picture_urls}
"""
        return init_input_str.format(
            product_name=self.product_name,
            product_url=self.product_url,
            total_budget=self.total_budget,
            total_days=self.total_days,
            picture_urls=json.dumps(self.product_picture_urls)
        )


# Meta Ads Marketing plan data type
class MetaAdsAccountInfo(BaseModel):
    """The Meta Ads account information for current marketing session."""
    account_id: str
    account_name: str
    amount_spent: float
    balance: float
    currency: str
    timezone_name: str
    dsa_required: bool
    dsa_compliance_note: str

    page_id: str
    page_name: str
    page_category: str
    page_link: str
    page_picture_url: str


class MetaAdsCampaign(BaseModel):   
    campaign_id: str = Field(description="The id of the campaign")
    name: str = Field(description="The name of the campaign")
    objective: str = Field(description="The objective of the campaign")
    status: str = Field(description="The status of the campaign")
    # budget related fields
    daily_budget: Optional[float] = Field(default=None, description="The daily budget for the campaign, in USD")
    lifetime_budget: Optional[float] = Field(default=None, description="The lifetime budget for the campaign, in USD")
    use_adset_level_budgets: bool = Field(default=True, description="True, if the budgets will be set at the ad set level instead of campaign level")
    is_adset_budget_sharing_enabled: bool = Field(default=False, description="True, if the budgets will be shared between the ad sets in the campaign")

    buying_type: Optional[str] = Field(default=None, description="The buying type for the campaign")
    bid_strategy: Optional[str] = Field(default=None, description="The bid strategy for the campaign")
    start_time: Optional[str] = Field(default=None, description="The start time for the campaign")
    stop_time: Optional[str] = Field(default=None, description="The stop time for the campaign")
    created_time: Optional[str] = Field(default=None, description="The created time for the campaign")
    updated_time: Optional[str] = Field(default=None, description="The updated time for the campaign")

    adsets: Optional[List[str]] = Field(default_factory=list, description="The list of ad set ids in the campaign")


class MetaAdsAdSet(BaseModel):
    ad_set_id: str = Field(default="", description="The id of the ad set")
    campaign_id: str = Field(default="", description="The id of the campaign this ad set belongs to")
    name: str = Field(description="The name of the ad set")
    status: str = Field(description="The status of the ad set")
    daily_budget: Optional[float] = Field(default=None, description="The daily budget for the ad set, in USD")
    lifetime_budget: Optional[float] = Field(default=None, description="The lifetime budget for the ad set, in USD")
    optimization_goal: str = Field(description="The optimization goal for the ad set")
    billing_event: str = Field(description="The billing event for the ad set")
    bid_amount: Optional[int] = Field(default=None, description="The bid amount for the ad set")
    bid_strategy: Optional[str] = Field(default=None, description="The bid strategy for the ad set")
    destination_type: Optional[str] = Field(default=None, description="The destination type for the ad set")
    start_time: Optional[str] = Field(default=None, description="The start time for the ad set")
    stop_time: Optional[str] = Field(default=None, description="The stop time for the ad set")
    created_time: Optional[str] = Field(default=None, description="The created time for the ad set")
    updated_time: Optional[str] = Field(default=None, description="The updated time for the ad set")
    is_dynamic_creative: Optional[bool] = Field(default=None, description="True, if the ad set is using dynamic creative")

    targeting: Optional[str] = Field(default=None, description="The targeting for the ad set")
    frequency_control_specs: Optional[List[str]] = Field(default=None, description="The frequency control specs for the ad set")

    ads: Optional[List[str]] = Field(default_factory=list, description="Ids of ads in the Adset")


class MetaAdsAd(BaseModel):
    ad_id: str = Field(default="", description="The id of the ad")
    adset_id: str = Field(default="", description="The id of the ad set this ad belongs to")
    campaign_id: str = Field(default="", description="The id of the campaign this ad belongs to")
    creative_id: str = Field(description="The id of the creative for the ad")
    name: str = Field(description="The name of the ad")
    status: str = Field(description="The status of the ad")
    preview_shareable_link: Optional[str] = Field(default=None, description="The preview shareable link for the ad")
    bid_amount: Optional[int] = Field(default=None, description="The bid amount for the ad")
    tracking_specs: Optional[List[str]] = Field(default=None, description="The tracking specs for the ad")


class MetaAdsCreative(BaseModel):
    creative_id: str = Field(default="", description="The id of the creative")
    image_hash: str = Field(description="The image hash in Meta Ads for the creative")
    page_id: str = Field(description="The page id in Meta Ads for the creative")
    link_url: Optional[str] = Field(default=None, description="The link url for the creative")
    image_url: Optional[str] = Field(default=None, description="The image url for the creative")
    message: Optional[str] = Field(default=None, description="The message for the creative")
    headline: Optional[str] = Field(default=None, description="The headline for the creative")
    headlines: Optional[List[str]] = Field(default=None, description="The headlines for the creative")
    description: Optional[str] = Field(default=None, description="The description for the creative")
    descriptions: Optional[List[str]] = Field(default=None, description="The descriptions for the creative")
    dynamic_creative_spec: Optional[str] = Field(default=None, description="The dynamic creative spec for the creative")


class MetaAdsImage(BaseModel):
    image_hash: str = Field(description="The image hash in Meta Ads for the image")
    image_name: Optional[str] = Field(default=None, description="The name of the image")
    image_url: Optional[str] = Field(default=None, description="The image url for the image")
    image_base64: Optional[str] = Field(default=None, description="The base64 encoded string of the image")
    image_mime_type: Optional[str] = Field(default=None, description="The mime type of the image, e.g., image/jpeg, image/png")


class MarketingHistory(BaseModel):
    """
    The history marketing data of a product summarized by the agent.
    Read only.
    """
    marketing_id: str
    marketing_input: str
    init_marketing_plan: str
    marketing_summary: str
    marketing_update_logs: Optional[List[str]]
    created_at: str
    finished_at: str

    def to_str(self) -> str:
        hist_str = """Finished marketing plan: {id} 
Input: {marketing_input}.
Created at: {created_at},
Finished at: {finished_at},

The initial marketing plan is:
{init_marketing_plan}

The optional marketing update logs are:
{marketing_update_logs}

The summary of the marketing plan is:
{marketing_summary}
"""

        return hist_str.format(
            id=self.marketing_id,
            marketing_input=self.marketing_input,
            created_at=self.created_at,
            finished_at=self.finished_at,
            init_marketing_plan=self.init_marketing_plan,
            marketing_update_logs=self.marketing_update_logs,
            marketing_summary=self.marketing_summary
        )


class MarketingPlan(BaseModel):
    """
    Data class of the marketing plan.

    A marketing plan can contain one and only `MetaAdsCampaign` with its
    `MetaAdsAdSet`, `MetaAdsAd`.

    A marketing plan can be updated multiple times (by the agent) to refine itself.
    The update details will be logged (by the agent).
    After the marketing plan is deleted / paused (finished but archieved),
    all the update logs will be added to a `MarketingHistory`.

    status:
        - INITIALIZED: after created, 
        - ACTIVE: the campaign is running
        - PAUSED: the campaign is paused
        - DELETED: after all the meta assets are deleted
    """
    plan_id: str
    status: MarketingPlanStatus = Field(default=MarketingPlanStatus.INITIALIZED)
    marketing_init_input: MarketingInitInput
    # after reasearch
    reasearch_res: Optional[str] = Field(default=None)
    # meta
    meta_ads_campaign: Optional[MetaAdsCampaign] = Field(default=None, description="The Meta Ads campaign for the plan")
    meta_ads_adsets: Optional[List[MetaAdsAdSet]] = Field(default_factory=list, description="The list of Meta Ads ad sets for the plan")
    meta_ads_ads: Optional[List[MetaAdsAd]] = Field(default_factory=list, description="The ads used in the plan")
    # log
    created_time: Optional[str] = None
    updated_time: Optional[str] = None
    deleted_time: Optional[str] = None
    start_time: Optional[str]   = None
    stop_time: Optional[str]    = None

    update_logs: Optional[List[str]] = Field(default_factory=list, description="Update logs summarized by the agent.")
    is_finished: bool = Field(default=False)
    in_history: bool = Field(default=False)

    def convert_to_history(self) -> MarketingHistory:
        assert self.is_finished, "Marketing is not finished, can not summary."
        hist = MarketingHistory(
            marketing_id=self.plan_id,
            marketing_input=self.marketing_init_input.to_str(),
            init_marketing_plan=self.update_logs[0],
            marketing_summary=self.update_logs[-1],
            marketing_update_logs=self.update_logs[1:-1],
            created_at=self.created_time,
            finished_at=self.deleted_time if self.deleted_time is not None else self.stop_time
        )
        self.in_history = True
        return hist


# workflow
# class WorkFlowInput(BaseModel):
#     """
#     The input of workflow of only one product.
#     """
#     marketing_init_input: MarketingInitInput
#     marketing_historys: Optional[List[MarketingHistory]] = Field(default_factory=list)


class WorkFlowSession(BaseModel):
    session_id: str
    status: WorkflowStatus = WorkflowStatus.INITIALIZED