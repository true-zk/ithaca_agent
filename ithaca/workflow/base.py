from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
import json
from uuid import uuid4

from ithaca.workflow.data_type import (
    MarketingPlan,
    MarketingPlanStatus,
    # WorkFlowInput,
    WorkflowStatus,
    WorkFlowSession,
    MetaAdsAccountInfo,
    MarketingInitInput,
    MarketingHistory,
)
from ithaca.agents import (
    BaseAgent,
    AgentFactory,
    ResearchAgent, ResearchAgentInput,
    PlanAgent, PlanAgentInput,
    UpdateAgent,
    SummaryAgent,
)
from ithaca.tools.meta_api import (
    get_ad_accounts_tool,
    get_ad_account_info_tool,
    get_pages_for_account_tool,
    get_pages_by_name_tool,
)
from ithaca.logger import logger


class BaseWorkFlow(ABC):
    def __init__(
        self
    ):
        # initialize
        self.user_account_info = self._get_user_account_info() 
        self.agents = self._build_agents()
        self.session = WorkFlowSession(
            session_id=f"session_{uuid4()}",
            status=WorkflowStatus.INITIALIZED
        )
        logger.info(f"[Workflow] Workflow is initialized ...")

    def _get_user_account_info(
        self, 
        account_id: Optional[str] = None, 
        page_name: Optional[str] = None
    ) -> MetaAdsAccountInfo:
        """
        Get user's ads account and pages.
        Defaulty gets the accessible adaccounts and pages for user_id: 'me'

        If provided account_id and page_name, check if the account_id is
        accessible and search the pages according to the page_name for the
        adaccount.
        """
        account_info = {}

        # get an account_id
        if not account_id:
            accounts = get_ad_accounts_tool()
            if 'data' in accounts and len(accounts['data']) > 0:
                account_id = accounts['data'][0]['id']
            else:
                raise ValueError("No accessible ad accounts found for the user.")
        
        # check accessible
        res = get_ad_account_info_tool(account_id)
        if "error" in res:
            logger.error(json.dumps(res))
            raise ValueError(f"Can not access account: {account_id}, check log for details.")
        
        account_info['account_id'] = account_id
        account_info['account_name'] = res['name']
        account_info['amount_spent'] = res['amount_spent']
        account_info['balance'] = res['balance']
        account_info['currency'] = res['currency']
        account_info['timezone_name'] = res['timezone_name']
        account_info['dsa_required'] = res['dsa_required']
        account_info['dsa_compliance_note'] = res['dsa_compliance_note']
        
        # get page
        if page_name:
            try:
                pages = get_pages_by_name_tool(account_id, page_name)
                logger.info(f"Find {pages['total_available']} pages, use first one.")
                page = pages['data'][0]
            except Exception as e:
                logger.error(f"Can not get pages from response: {res}")
                raise e
        else:
            try:
                pages = get_pages_for_account_tool(account_id)
                logger.info(f"Find {pages['total_pages_found']} pages, use first one.")
                page = pages['data'][0]
            except Exception as e:
                logger.error(f"Can not get pages from response: {res}")
                raise e

        account_info['page_id'] = page['id']
        account_info['page_name'] = page['name']
        account_info['page_category'] = page['category']
        account_info['page_link'] = page['link']
        account_info['page_picture_url'] = page['picture']['data']['url']

        return MetaAdsAccountInfo(
            **account_info
        )

    def _build_agents(self) -> Dict[str, BaseAgent]:
        agents = AgentFactory.build_all()
        
        self.research_agent: ResearchAgent = agents['research']
        self.plan_agent: PlanAgent = agents['plan']
        self.update_agent: UpdateAgent = agents['update']
        self.summary_agent: SummaryAgent = agents['summary']
        return agents

    # nodes, process marketing
    def research_step(
        self,
        product_name: str,
        product_url: str,
        picture_urls: List[str],
        addi_data: Dict[str, Any] = {}
    ) -> Dict[str, Any]:
        """
        Return:
            {
                "picture_urls": List[str],
                "keywords": List[str],
                "research_summary": str
            }
        """
        input = ResearchAgentInput(
            product_name=product_name,
            product_url=product_url,
            picture_urls=picture_urls,
            additional_data=""
        )

        if 'total_budget' in addi_data:
            input.additional_data += f"The total budget of the marketing plan: {addi_data['total_budget']}\n"
        
        if 'total_days' in addi_data:
            input.additional_data += f"The max total days to execute the marketing plan: {addi_data['total_days']}"

        out = self.research_agent.run(input)

        return out
    
    def plan_step(
        self,
        product_name: str,
        product_url: str,
        picture_urls: List[str],
        research_summary: str,
        account_info: MetaAdsAccountInfo,
        total_budget: Optional[float] = None,
        total_days: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Return:
            {
                "campaign": MetaAdsCampaign,
                "adsets": List[MetaAdsAdSet],
                "ads": List[MetaAdsAd],
                "creatives": List[MetaAdsCreative],
                "images": List[MetaAdsImage]
            }
        """
        input = PlanAgentInput(
            product_name=product_name,
            product_url=product_url,
            picture_urls=picture_urls,
            research_summary=research_summary,
            account_info=account_info,
            total_budget=total_budget
        )
        if total_days is not None:
            input.total_days = total_days
        out = self.plan_agent.run(input)
        return out
    
    def update_step(self, plan: MarketingPlan) -> Dict[str, Any]:
        """
        Update the step of the workflow.
        Return the updated plan with details and messages.
        {
            "updated_plan": Dict[str, Any],
            "update_details": str,
        }
        """
        out = self.update_agent.run(plan)
        return out
    
    def summary_step(self, plan: MarketingPlan) -> str:
        """
        Summary the step of the workflow.
        Return the summary of the plan.
        """
        out = self.summary_agent.run(plan)
        return out

    @abstractmethod
    def run(self) -> bool:
        """
        Run the workflow.
        """
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    def __str__(self) -> str:
        raise NotImplementedError("Subclasses must implement this method")
