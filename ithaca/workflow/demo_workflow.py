"""
A demo workflow only supports single product.

work flow
input (basic product info with optional hist) -> 
get account info ->
research -> marketing_plan initialized ->
plan     -> marketing_plan paused      ->
human_in_the_loop (optional)    -> active   ->
update (get insights, update, log)  ->
finished (human_in_the_loop or budget or time) ->
convert_to_hist
"""
from typing import List, Dict, Any, Optional
from uuid import uuid4
import json
from datetime import datetime

from ithaca.workflow.base import BaseWorkFlow
from ithaca.workflow.data_type import (
    MarketingHistory,
    MarketingInitInput,
    MarketingPlan,
    MarketingPlanStatus,
    WorkflowStatus,
)
from ithaca.logger import logger


class EpochSchedule:
    current_epoch: int = 0
    def __init__(
        self,
        interval_seconds: int,
        total_epochs: int
    ):
        self.interval_seconds = interval_seconds
        self.total_epochs = total_epochs
    
    def reset(self):
        self.current_epoch = 0
    
    def step(self):
        self.current_epoch += 1
    
    def is_finished(self) -> bool:
        return self.current_epoch >= self.total_epochs

    def get_current_epoch(self) -> int:
        return self.current_epoch


class DemoWorkFlow(BaseWorkFlow):
    """
    The demo workflow.
    """
    
    def __init__(
        self,
        marketing_input: MarketingInitInput,
        schedule_config: Optional[Dict[str, Any]] = None,
        marketing_hist: Optional[List[MarketingHistory]] = None
    ):
        self.plan_init_input = marketing_input
        self.schedule_config = schedule_config if schedule_config else {
            "interval_seconds": 3600 * 24,   # a day
            "finish_type": "epoches",
            "finish_value": 7,
        }
        # set schedule
        # TODO: for demo, use epoch schedule only,
        # TODO: we need to abstract the schedule logic
        # TODO: in the future
        self.schedule = EpochSchedule(
            interval_seconds=self.schedule_config["interval_seconds"],
            total_epochs=self.schedule_config["finish_value"]
        )
        self.schedule.reset()
        self.hist = marketing_hist if marketing_hist else []
        self.plan = self._initialize_plan()
        super().__init__()
    
    def _initialize_plan(self) -> MarketingPlan:
        return MarketingPlan(
            plan_id=f"plan_{uuid4()}",
            status=MarketingPlanStatus.INITIALIZED,
            marketing_init_input=self.plan_init_input
        )

    def run(self):
        if self.session.status == WorkflowStatus.INITIALIZED:
            self.init_run()
        elif self.session.status == WorkflowStatus.EXECUTING:
            self.loop_run()
        elif self.session.status == WorkflowStatus.COMPLETED:
            self.finish_run()
        else:
            raise ValueError(f"Invalid workflow status: {self.session.status}")

    def init_run(self):
        # step 1, research
        addi_data = {}
        if self.plan_init_input.total_budget is not None:
            addi_data["total_budget"] = self.plan_init_input.total_budget
        if self.plan_init_input.total_days is not None:
            addi_data["total_days"] = self.plan_init_input.total_days
        research_res = self.research_step(
            product_name=self.plan_init_input.product_name,
            product_url=self.plan_init_input.product_url,
            picture_urls=self.plan_init_input.product_picture_urls,
            addi_data=addi_data
        )
        self.plan.reasearch_res = research_res["research_summary"]
        print(f"Research result: {research_res}")

        # step 2, plan and execute
        plan_res = self.plan_step(
            product_name=self.plan_init_input.product_name,
            product_url=self.plan_init_input.product_url,
            picture_urls=research_res["picture_urls"],
            research_summary=research_res["research_summary"],
            account_info=self.user_account_info,
            total_budget=self.plan_init_input.total_budget,
            total_days=self.plan_init_input.total_days
        )
        self.plan.meta_ads_campaign = plan_res["campaign"]
        self.plan.meta_ads_adsets = plan_res["adsets"]
        self.plan.meta_ads_ads = plan_res["ads"]
        self.plan.update_logs.append(f"Plan created: {json.dumps(plan_res)}")
        self.plan.created_time = datetime.now().isoformat()
        self.plan.start_time = datetime.now().isoformat()
        self.plan.status = MarketingPlanStatus.ACTIVE
        self.session.status = WorkflowStatus.EXECUTING
        logger.info(f"[Workflow] Workflow is executing ...")
        print(f"Plan result: {plan_res}")

    def loop_run(self):
        logger.info(f"[Workflow] Workflow is executing ...")
        if not self.schedule.is_finished():
            self.schedule.step()
            logger.info(f"[Workflow] Workflow is executing epoch {self.schedule.get_current_epoch()} ...")
            #
            update_res = self.update_step(self.plan)
            self.plan.meta_ads_campaign = update_res["updated_plan"]["campaign"]
            self.plan.meta_ads_adsets = update_res["updated_plan"]["adsets"]
            self.plan.meta_ads_ads = update_res["updated_plan"]["ads"]
            self.plan.update_logs.append(f"Plan updated: {update_res['update_details']}")
            self.plan.updated_time = datetime.now().isoformat()
            self.plan.status = MarketingPlanStatus.ACTIVE
            self.session.status = WorkflowStatus.EXECUTING
            logger.info(f"[Workflow] Workflow is executing ...")
            print(f"Update result: {update_res}")

        else:
            self.session.status = WorkflowStatus.COMPLETED
            logger.info(f"[Workflow] Workflow is completed ...")

    def finish_run(self, force_delete: bool = False):

        self.plan.status = MarketingPlanStatus.PAUSED
        self.plan.stop_time = datetime.now().isoformat()
        
        summary_res = self.summary_step(self.plan)
        self.plan.update_logs.append(f"Summary: {summary_res}")
        self.plan.is_finished = True

        if force_delete:
            self.plan.status = MarketingPlanStatus.DELETED
            self.plan.deleted_time = datetime.now().isoformat()
            self._force_delete_plan()

        self.session.status = WorkflowStatus.FINISHED
        logger.info(f"[Workflow] Workflow is finished ...")
    
    def _force_delete_plan(self):
        raise NotImplementedError("Subclasses must implement this method")

    def __str__(self):
        return (
            f"DemoWorkFlow with{"out" if not self.hist else ""} history:\n\n"
            f"Input:\n"
            f"{self.plan_init_input.to_str()}"
        )
