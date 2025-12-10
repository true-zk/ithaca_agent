"""
Research agent
"""
from typing import List, Callable, Dict, Any, Optional
from pydantic import BaseModel, Field
import json

from ithaca.agents.base import BaseAgent
from ithaca.workflow.data_type import (
    MetaAdsCampaign, 
    MetaAdsAccountInfo,
    MetaAdsAdSet,
    MetaAdsAd,
    MetaAdsCreative,
    MetaAdsImage
)
from ithaca.tools.meta_api import (
    create_campaign_tool,
    create_adset_tool,
    create_ad_tool,
    create_single_image_creative,
    upload_ad_image_tool,
    get_campaign_details_tool,
    get_adset_details_tool,
    get_ad_details_tool,
    get_creative_details_tool
)
from ithaca.logger import logger
from ithaca.utils import get_skill_by_file_name


class PlanAgentInput(BaseModel):
    product_name: str
    product_url: str
    picture_urls: List[str]
    research_summary: str
    # account info
    account_info: MetaAdsAccountInfo

    # Meta ads campaign related fields
    total_budget: Optional[float] = Field(
        default=None, 
        description="The total budget for the campaign, in USD. If None, use the remaining budget of the ad account"
    )
    total_days: Optional[int] = Field(
        default=7, 
        description="The total days for the campaign to execute. If None, use the 7 days for the campaign"
    )


class PlanAgentContext(BaseModel):
    account_info: MetaAdsAccountInfo = Field(default=None, description="The account info for the plan")
    messages: List[dict[str, Any]] = Field(default_factory=list, description="The list of messages for the plan")
    # campaign related fields
    campaign: MetaAdsCampaign = Field(default=None, description="The campaign for the plan")
    adsets: List[MetaAdsAdSet] = Field(default_factory=list, description="The list of ad sets for the plan")
    ads: List[MetaAdsAd] = Field(default_factory=list, description="The list of ads for the plan")
    creatives: List[MetaAdsCreative] = Field(default_factory=list, description="The list of creatives for the plan")
    images: List[MetaAdsImage] = Field(default_factory=list, description="The list of images for the plan")


class PlanAgent(BaseAgent):
    def __init__(
        self,
        name: str = "CampaignAgent",
        max_retry: int = 3,
    ):
        model = "gemini-3-pro-preview"  # support schema output with tools
        tools = []  # dynamically add tools based on the stage
        system_prompt = self._build_system_prompt()
        super().__init__(name=name, model=model, tools=tools, max_retry=max_retry, system_prompt=system_prompt)
    
    def _build_system_prompt(self) -> str:
        prompt = f"""
        You are a plan agent.
        You are responsible for creating a Meta Ads marketing plan 
        for the given product step by step.

        The whole marketing plan should be created in the following hierarchy:
        - Campaign: The top level object, containing ad sets. Only one. 
            Campaign is used to decide the blueprint of the marketing plan without details.
        - Ad Set: Ad set is the budget and schedule unit. 
            You should create some different ad sets for the campaign to search 
            the marketing places.
            A ad set must belong to a campaign.
        - Ad: Ad is the real presentation unit. 
            An ad must belong to a ad set.
        - Creative: Creative is the content of the ad.
            A creative must belong to an ad.
        
        Because the Meta Ads API has strict constrains, 
        you should create the marketing plan step by step.
        At each step, you are given the context of the previous steps.
        The next step should be based on the context of the previous steps
        and new instructions.

        At each step, you will be provided the useful tools to create the objects.
        """
        return prompt

    def _build_init_prompt(self, input: PlanAgentInput) -> str:
        if input.total_budget is None:
            total_budget = input.account_info.balance
        else:
            total_budget = input.total_budget
        total_budget = f"{total_budget} {input.account_info.currency}"

        prompt = f"""
        User want to create a marketing plan for the product {input.product_name}.
        You are a plan agent. 
        You are responsible for creating a marketing plan for the product step by step.
        You are given the following basic information:
            - Product name: {input.product_name}
            - Product url: {input.product_url}
            - Product picture urls: {input.picture_urls}
            - Research summary: {input.research_summary}
            - Total budget for the plan: {total_budget}
            - Total days for the plan: {input.total_days}

        The user's Meta Ads account info (including ad account and page info):
        {input.account_info.model_dump_json()}
        """
        return prompt

    def _build_prompt_with_context(self, context: PlanAgentContext) -> str:

        messages = context.messages
        msg_str = ""
        for idx, msg in enumerate(messages):
            if idx == 0:
                msg_str += f"Initial instruction: {msg['instruction']}\n"
            else:
                msg_str += f"Step {idx+1}:\n"
                msg_str += f"Instruction: {msg['instruction']}\n"
                msg_str += f"LLM Response: {msg['response']}\n"

        prompt = f"""
        You are given the following context of the previous steps:
        {msg_str}
        Now, you will be given the new instructions.
        """
        return prompt

    def _create_campaign(self, context: PlanAgentContext, input: PlanAgentInput) -> PlanAgentContext:
        init_prompt = self._build_init_prompt(input)
        context.messages.append({
            "instruction": init_prompt,
        })
        logger.info(f"[PlanAgent] Initial instruction: {init_prompt}")

        campaign_prompt = """Now, you should call the create_campaign tool to create and execute the campaign.
After the campaign is created, you should call get_campaign_details tool to get the campaign details.
Then, you should return the campaign details in a json format.
The created campaign should be 'ACTIVE' status.
"""
        prompt = init_prompt + campaign_prompt

        campaign_tools = [
            create_campaign_tool,
            get_campaign_details_tool,
        ]

        campaign_schema = MetaAdsCampaign.model_json_schema()

        try:
            # execute the tool
            raw_res = self._generate_once(
                prompt=prompt,
                # schema=campaign_schema,
                tools=campaign_tools,
            )
            # schema output
            schema_prompt = f"""
            You are given the following campaign details:
            {raw_res}
            Please return the campaign details in a given schema format.
            Schema: {campaign_schema}
            """
            res = self._generate_once(
                prompt=schema_prompt,
                schema=campaign_schema,
            )
            res = MetaAdsCampaign.model_validate(res)
            context.campaign = res
            context.messages.append({
                "instruction": campaign_prompt,
                "response": f"Campaign created: {res.model_dump_json()}\n\n Campaign created with ad set level budgets. Set budgets when creating ad sets within this campaign."
            })
            logger.info(f"[PlanAgent] Campaign created: {res.model_dump_json()}")
            return context

        except Exception as e:
            logger.error(f"[PlanAgent] Error creating campaign: {e}")
            raise e
    
    def _create_adsets(self, context: PlanAgentContext) -> PlanAgentContext:
        context_prompt = self._build_prompt_with_context(context)
        adsets_prompt = """Now, you should call the create_adset tool to create and execute some different ad sets for the campaign.
After the ad sets are created, you should call get_adset_details tool to get the ad set details.
Then, you should return the ad set details like a list in a json format.

- Set budgets when creating ad sets within this campaign.
- The budget
- You are provided with the skill to create ad sets. Please follow the skill to create ad sets.
- The created ad sets should be 'ACTIVE' status.
"""
        adsets_skill = get_skill_by_file_name("create_adsets.txt")  # 2736 tokens
        prompt = context_prompt + adsets_prompt + "\n\n" + "Skill: " + adsets_skill

        adsets_tools = [
            create_adset_tool,
            get_adset_details_tool,
            # {"url_context": {}},
            # {"google_search": {}}
        ]

        class ListAdSets(BaseModel):
            adsets: List[MetaAdsAdSet] = Field(default_factory=list, description="The list of ad sets created")
        adsets_schema = ListAdSets.model_json_schema()

        try:
            # execute the tool
            raw_res = self._generate_once(
                prompt=prompt,
                # schema=adsets_schema,
                tools=adsets_tools,
                max_tokens=10000,
            )
            # schema output
            schema_prompt = f"""
            You are given the following ad set details:
            {raw_res}
            Please return the ad set details in a given schema format.
            Schema: {adsets_schema}
            """
            res = self._generate_once(
                prompt=schema_prompt,
                schema=adsets_schema,
            )
            res = ListAdSets.model_validate(res)
            context.adsets.extend(res.adsets)
            context.messages.append({
                "instruction": adsets_prompt,
                "response": f"Ad sets created: {res.model_dump_json()}"
            })
            logger.info(f"[PlanAgent] Ad sets created: {res.model_dump_json()}")
            return context
        except Exception as e:
            logger.error(f"[PlanAgent] Error creating ad sets: {e}")
            raise e
    
    def _create_ads(self, context: PlanAgentContext, picture_urls: List[str]) -> PlanAgentContext:
        # 1. upload images to Meta Ads
        for image in picture_urls:
            upload_image_res = upload_ad_image_tool(context.account_info.account_id, image_url=image)
            image_hash = upload_image_res["image_hash"]
            context.images.append(MetaAdsImage(image_hash=image_hash, image_url=image))
            context.messages.append({
                "instruction": f"Upload image {image} to Meta Ads and get the image hash",
                "response": f"Image uploaded: {image_hash}"
            })
            logger.info(f"[PlanAgent] Image uploaded: {image_hash}")
        # 2. create creatives
        context_prompt = self._build_prompt_with_context(context)
        creatives_prompt = f"""Now, you should call the create_single_image_creative tool to create the creatives.
After the creatives are created, you should call get_creative_details tool to get the creative details.
Then, you should return the creative details like a list in a json format.
The images to be used for the creatives are: {context.images}
"""
        prompt = context_prompt + creatives_prompt

        creative_tools = [
            create_single_image_creative,
            get_creative_details_tool,
        ]

        class ListCreatives(BaseModel):
            creatives: List[MetaAdsCreative] = Field(default_factory=list, description="The list of creatives created")
        creative_schema = ListCreatives.model_json_schema()

        try:
            # execute the tool
            raw_res = self._generate_once(
                prompt=prompt,
                # schema=creative_schema,
                tools=creative_tools,
            )
            # schema output
            schema_prompt = f"""
            You are given the following creative details:
            {raw_res}
            Please return the creative details in a given schema format.
            Schema: {creative_schema}
            """
            res = self._generate_once(
                prompt=schema_prompt,
                schema=creative_schema,
            )
            res = ListCreatives.model_validate(res)
            context.creatives.extend(res.creatives)
            context.messages.append({
                "instruction": creatives_prompt,
                "response": f"Creatives created: {res.model_dump_json()}"
            })
            logger.info(f"[PlanAgent] Creatives created: {res.model_dump_json()}")
        except Exception as e:
            logger.error(f"[PlanAgent] Error creating creatives: {e}")
            raise e
        # 3. create ads
        context_prompt = self._build_prompt_with_context(context)
        ads_prompt = f"""Now, you should call the create_ad tool to create and execute the ads for each ad set.
You should plan and decide the ad for each ad set.
After the ads are created, you should call get_ad_details tool to get the ad details.
Then, you should return the ad details like a list in a json format.
The creatives to be used for the ads are: {context.creatives}
The created ads should be 'ACTIVE' status.
"""
        prompt = context_prompt + ads_prompt

        ads_tools = [
            create_ad_tool,
            get_ad_details_tool,
        ]

        class ListAds(BaseModel):
            ads: List[MetaAdsAd] = Field(default_factory=list, description="The list of ads created")
        ads_schema = ListAds.model_json_schema()

        try:
            # execute the tool
            raw_res = self._generate_once(
                prompt=prompt,
                # schema=ads_schema,
                tools=ads_tools,
            )

            # schema output
            schema_prompt = f"""
            You are given the following ad details:
            {raw_res}
            Please return the ad details in a given schema format.
            Schema: {ads_schema}
            """
            res = self._generate_once(
                prompt=schema_prompt,
                schema=ads_schema,
            )
            res = ListAds.model_validate(res)
            context.ads.extend(res.ads)
            context.messages.append({
                "instruction": ads_prompt,
                "response": f"Ads created: {res.model_dump_json()}"
            })
            logger.info(f"[PlanAgent] Ads created: {res.model_dump_json()}")
        except Exception as e:
            logger.error(f"[PlanAgent] Error creating ads: {e}")
            raise e

        return context    

    def run(self, input: PlanAgentInput) -> PlanAgentContext:
        # step 0, build initial context
        context = PlanAgentContext(
            account_info=input.account_info,
            messages=[]
        )
        logger.info("[PlanAgent] Step 0: PlanAgentContext: %s", context.model_dump_json())
        # step 1, create campaign
        context = self._create_campaign(context, input)
        logger.info("[PlanAgent] Step 1: PlanAgentContext: %s", context.model_dump_json())
        # step 2, create ad sets
        context = self._create_adsets(context)
        logger.info("[PlanAgent] Step 2: PlanAgentContext: %s", context.model_dump_json())
        # step 3, create ads
        context = self._create_ads(context, input.picture_urls)
        logger.info("[PlanAgent] Step 3: PlanAgentContext: %s", context.model_dump_json())

        cache_file = self._cache_context(context.model_dump())
        logger.info(f"[PlanAgent] Cached context to {cache_file}")

        return context.model_dump()