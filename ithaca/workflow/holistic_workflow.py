from typing import Any, List, Dict, Callable

from ithaca.agents import HolisticAgent, EvaluationAgent
from ithaca.agents.agent_types import (
    HolisticInput,
    HolisticOutput, 
    EvaluationInput, 
    EvaluationOutput,
    MarketingPlan,
)
from ithaca.workflow.base import BaseWorkFlow
from ithaca.db import IthacaDB
from ithaca.oauth import auth_manager
from ithaca.logger import logger


class HolisticWorkflow(BaseWorkFlow):

    on_going_plans: List[MarketingPlan] = []

    def __init__(
        self,
        input: HolisticInput
    ):
        self.init_input = input

        # Oauth Meta Ads if not
        if auth_manager.get_access_token() is None:
            auth_manager.authenticate()
            logger.info(f"Meta Ads authenticated with access token: {auth_manager.get_access_token()[:10]}...")
        else:
            logger.info(f"Meta Ads already authenticated with access token: {auth_manager.get_access_token()[:10]}...")

        # Build agents
        self.build_agents()

        # Check db avaliable
        IthacaDB.check_db_available(force=True)

        logger.info("Holistic workflow is ready.")
        
    def build_agents(self):
        self.holistic_agent = HolisticAgent()
        self.evaluation_agent = EvaluationAgent()
        logger.info("Holistic and evaluation agents are built successfully.")

    async def init_run(self) -> bool:
        """Run with init input (without marketing history)"""
        try:
            agent_res = await self.holistic_agent.run(self.init_input)
            logger.info(f"Holistic agent response: {agent_res['response']}")
            output: HolisticOutput = agent_res['parsed_output']
            output.save_to_db()
            self.on_going_plans = output.marketing_plans
            logger.info(f"On going plans: {[plan.plan_uuid for plan in self.on_going_plans]}")
            return True
        except Exception as e:
            logger.error(f"Error occurs in running: {e}")
            return False

    async def run(self) -> bool:
        """Run with marketing history"""
    
        try:
            # TODO: Keep history_marketing_plans as None, auto extract in agent
            # TODO: Refine this 
            eval_input = EvaluationInput(
                product_name=self.init_input.product_name,
                product_url=self.init_input.product_url,
                new_marketing_plans=self.on_going_plans,
                total_budget=self.init_input.total_budget
            )
            logger.info(f"Evaluation input: {eval_input}")
            agent_res = await self.evaluation_agent.run(eval_input)
            logger.info(f"Evaluation agent response: {agent_res['response']}")
            output: EvaluationOutput = agent_res['parsed_output']
            output.update_to_db()

            self.on_going_plans = []

            holistic_input = HolisticInput(
                product_name=self.init_input.product_name,
                product_url=self.init_input.product_url,
                total_budget=self.init_input.total_budget,
            )
            logger.info(f"Holistic input: {holistic_input}")
            agent_res = await self.holistic_agent.run(holistic_input)
            logger.info(f"Holistic agent response: {agent_res['response']}")
            output: HolisticOutput = agent_res['parsed_output']
            output.save_to_db()
            self.on_going_plans = output.marketing_plans
            logger.info(f"On going plans: {[plan.plan_uuid for plan in self.on_going_plans]}")
            return True
        except Exception as e:
            logger.error(f"Error occurs in running: {e}")
            return False

    def __str__(self) -> str:
        return "Holistic Workflow"