"""
Update agent
"""
from typing import List, Callable, Dict, Any, Optional
from pydantic import BaseModel, Field

from google.genai import types

from ithaca.agents.base import BaseAgent
from ithaca.workflow.data_type import (
    MetaAdsCampaign, 
    MetaAdsAccountInfo,
    MetaAdsAdSet,
    MetaAdsAd,
    MetaAdsCreative,
    MetaAdsImage,
    MarketingPlan
)
from ithaca.tools.meta_api.meta_ads_insights import (
    get_campaign_insights_tool,
    get_adset_insights_tool,
    get_ad_insights_tool
)
from ithaca.tools.meta_api.meta_ads_adset import (
    update_adset_tool,
)
from ithaca.tools.meta_api.meta_ads_ad import (
    update_ad_tool,
)
from ithaca.tools.meta_api import (
    upload_ad_image_tool,
    create_single_image_creative,
    get_campaign_details_tool,
    get_adset_details_tool,
    get_ad_details_tool,
)
from ithaca.logger import logger


class UpdateAgentContext(BaseModel):
    plan: MarketingPlan
    updated_plan: Optional[Dict[str, Any]] = Field(default=None, description="The updated marketing plan, in a dict format")
    update_details: Optional[str] = Field(default=None, description="The update details, in a string format")
    messages: List[dict[str, Any]] = Field(default_factory=list, description="The list of messages for the plan")


class UpdateAgent(BaseAgent):
    def __init__(
        self,
        name: str = "UpdateAgent",
        max_retry: int = 3,
    ):
        model = "gemini-3-pro-preview"
        tools = []
        system_prompt = self._build_system_prompt()
        super().__init__(name=name, model=model, tools=tools, max_retry=max_retry, system_prompt=system_prompt)
    
    def _build_system_prompt(self) -> str:
        prompt = f"""
        You are a update agent.
        You are responsible for updating the marketing plan step by step.
        You should check the performance of the marketing plan
        and analyze the direction to updat, and give instructions.
        Then you should update the marketing plan.
        You should focus on the adsets and its budgets distribution.

        You will be provided with the useful tools to complete the task at eachstep.
        If you find error in tool response, you should try to solve it by yourself.
        """
        return prompt
    
    def _build_prompt_with_context(self) -> str:
        messages = self.context.messages
        msg_str = ""
        for idx, msg in enumerate(messages):
                msg_str += f"Step {idx+1}:\n"
                msg_str += f"Instruction: {msg['instruction']}\n"
                msg_str += f"LLM Response: {msg['response']}\n"

        prompt = f"""
        You are given the following context of the previous steps:
        {msg_str}
        Now, you will be given the new instructions.\n\n
        """
        return prompt
    
    def _build_plan_prompt(self) -> str:
        plan_prompt = f"""The running marketing plan is:
{self.context.plan.model_dump_json()} \n\n
"""
        return plan_prompt

    def _get_insight(self):

        insight_prompt = f"""For now, you should use tools to get the insight (performance) 
of the marketing plan, and analyze the direction to update.
1. You should use tools to get campaign / adsets / ads insights.
2. You should summary the performance of the marketing plan at adsets / ads level.
3. You should give suggestions on how to update adsets / ads.
4. Return the detailed summary and suggestions.
"""
        prompt = self._build_plan_prompt() + insight_prompt

        insight_tools = [
            get_campaign_insights_tool,
            get_adset_insights_tool,
            get_ad_insights_tool,
        ]

        try:
            raw_res = self._generate_once(
                prompt=prompt,
                tools=insight_tools,
            )
            self.context.messages.append({
                "instruction": insight_prompt,
                "response": raw_res,
            })
        except Exception as e:
            logger.error(f"[UpdateAgent] Error getting insights: {e}")
            raise e
        
    def _update_plan(self):
        update_prompt = f"""Now, you should update the marketing plan based on the insights.
You should call tools to update the adsets / ads in the marketing plan.
After the update, you should return a detailed summary of the update
including step by step how to update the marketing plan.

If you need to use new creatives, you should use tools to upload new images first,
then use the image hash to create new creatives.
After that, you should use tools to update the ads to use the new creatives.

If you encounter any error in the tools, you should try to solve it by yourself.
If the problem is not solvable, you should keep the original marketing plan.
And you should return the error details.
"""
        prompt = self._build_prompt_with_context() + update_prompt
        update_tools = [
            update_adset_tool,
            update_ad_tool,
            create_single_image_creative,
            upload_ad_image_tool,
        ]
        try:
            raw_res = self._generate_once(
                prompt=prompt,
                tools=update_tools,
            )
            self.context.update_details = raw_res
            self.context.messages.append({
                "instruction": update_prompt,
                "response": raw_res,
            })
            logger.info(f"[UpdateAgent] Update details: {raw_res}")
        except Exception as e:
            logger.error(f"[UpdateAgent] Error updating plan: {e}")
            raise e
    
    def _get_new_plan(self):
        class NewPlan(BaseModel):
            campaign: MetaAdsCampaign = Field(description="The campaign details")
            adsets: List[MetaAdsAdSet] = Field(description="The adset details")
            ads: List[MetaAdsAd] = Field(description="The ad details")
        new_plan_schema = NewPlan.model_json_schema()

        new_plan_prompt = f"""
Now, you have updated the marketing plan.
You should call tools to get the details of the updated marketing plan
including campaign / adsets / ads.
And you should return the details in a json format,
including campaign, list of adsets and list of ads.
Schema: {new_plan_schema}
"""
        prompt = self._build_prompt_with_context() + new_plan_prompt
        new_plan_tools = [
            get_campaign_details_tool,
            get_adset_details_tool,
            get_ad_details_tool,
        ]
        
        try:
            # execute the tool
            raw_res = self._generate_once(
                prompt=prompt,
                tools=new_plan_tools,
            )
            # schema output
            schema_prompt = f"""
            You are given the following new plan details including campaign, list of adsets and list of ads:
            {raw_res}
            Please return the new plan details in a given schema format.
            Schema: {new_plan_schema}
            """
            res = self._generate_once(
                prompt=schema_prompt,
                schema=new_plan_schema,
            )
            res = NewPlan.model_validate(res)
            self.context.updated_plan = res.model_dump()
            self.context.messages.append({
                "instruction": new_plan_prompt,
                "response": f"New plan: {res.model_dump_json()}",
            })
            logger.info(f"[UpdateAgent] New plan: {res.model_dump_json()}")
        except Exception as e:
            logger.error(f"[UpdateAgent] Error getting new plan: {e}")
            raise e
    
    def run(self, initial_plan: MarketingPlan) -> Dict[str, Any]:
        self.context = UpdateAgentContext(plan=initial_plan)
        self._get_insight()
        logger.info(f"[UpdateAgent] Insight: {self.context.update_details}")
        self._update_plan()
        logger.info(f"[UpdateAgent] Update details: {self.context.update_details}")
        self._get_new_plan()
        logger.info(f"[UpdateAgent] New plan: {self.context.updated_plan}")

        cache_file = self._cache_context(self.context.model_dump())
        logger.info(f"[PlanAgent] Cached context to {cache_file}")

        return {
            "updated_plan": self.context.updated_plan,
            "update_details": self.context.update_details,
        }
    
