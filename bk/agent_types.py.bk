from typing import Optional, List, TYPE_CHECKING
from pydantic import BaseModel, Field, field_validator
from datetime import datetime

from ithaca.db import IthacaDB
from ithaca.db.history import HistoryModel
from ithaca.logger import logger


# Common types for all agents
class MarketingPlanMixin:
    """
    Mixin for marketing plan.
    Provides common functionality for MarketingPlan and HistoryMarketingPlan.
    """
    if TYPE_CHECKING:
        # for type checking only
        plan_uuid: str
    
    def check_exist(self, plan_name: Optional[str] = None, plan_url: Optional[str] = None) -> bool:
        """
        Check if the marketing plan exists in the database.
        """
        filters = {"plan_uuid": self.plan_uuid}
        if plan_name is not None:
            filters["product_name"] = plan_name
        if plan_url is not None:
            filters["product_url"] = plan_url

        q_res = IthacaDB.query(
            HistoryModel, 
            filters=filters,
        )
        return len(q_res) > 0

    def to_history_model(self) -> Optional[HistoryModel]:
        """
        Convert the marketing plan to a history model.
        """
        if isinstance(self, HistoryMarketingPlan):
            return HistoryModel(
                product_name=None,
                product_url=None,
                plan_uuid=self.plan_uuid,
                plan_description=self.plan_description,
                plan_details=self.plan_details,
                budget=self.budget,
                actual_cost=self.actual_cost,
                plan_evaluation=self.plan_evaluation,
                plan_score=self.plan_score,
                created_at=self.created_at,
                evaluated_at=self.evaluated_at,
            )
        elif isinstance(self, MarketingPlan):
            return HistoryModel(
                product_name=None,
                product_url=None,
                plan_uuid=self.plan_uuid,
                plan_description=self.plan_description,
                plan_details=self.plan_details,
                budget=self.budget,
                actual_cost=None,  
                plan_evaluation=None,  
                plan_score=None,
                created_at=self.created_at,
                evaluated_at=None,
            )
        else:
            raise ValueError(f"Unsupported marketing plan type: {type(self)}")

    def save_to_history(self, product_name: str = None, product_url: str = None) -> bool:
        """
        Convenience method to convert and save to history database.
        If the plan already exists, return False.
        
        Returns:
            bool: True if saved successfully, False otherwise
        """
        try:
            history_model = self.to_history_model()
            if self.check_exist():
                logger.warning(f"History marketing plan {self.plan_uuid} already exists")
                return False
            
            history_model.product_name = product_name
            history_model.product_url = product_url
            
            success = IthacaDB.add(history_model)
            if success:
                logger.info(f"Successfully saved plan {self.plan_uuid} to history")
            else:
                logger.error(f"Failed to save plan {self.plan_uuid} to history")
            
            return success
            
        except Exception as e:
            logger.error(f"Error saving plan {self.plan_uuid} to history: {e}")
            return False


class MarketingPlan(BaseModel, MarketingPlanMixin):
    """
    Marketing plan schema for agent. 
    It contains the plan UUID, name, description, and structured tool calls.
    """
    plan_uuid: str = Field(description="Unique identifier for the marketing plan")
    plan_description: str = Field(description="Detailed description of the marketing plan strategy")
    plan_details: str = Field(description="Detailed todo with track of tool calls of the marketing plan")
    budget: float = Field(description="Budget for the marketing plan")
    created_at: datetime = Field(description="Timestamp of the creation of the marketing plan")


class HistoryMarketingPlan(BaseModel, MarketingPlanMixin):
    """
    History marketing plans.
    """
    plan_uuid: str = Field(description="Unique identifier for the marketing plan")
    plan_description: str = Field(description="Detailed description of the marketing plan strategy")
    plan_details: str = Field(description="Detailed todo with track of tool calls of the marketing plan")

    budget: float = Field(description="Budget for the marketing plan")
    actual_cost: float = Field(description="Actual cost of the marketing plan")

    plan_evaluation: str = Field(description="Evaluation summary of the history markerting paln")
    plan_score: float = Field(description="Score of the history plan, from 1 to 10")
    created_at: datetime = Field(description="Timestamp of the creation of the marketing plan")
    evaluated_at: datetime = Field(description="Timestamp of the evaluation of the marketing plan")

    @field_validator('plan_score')
    def validate_plan_score(cls, v):
        if v < 0 or v > 10:
            raise ValueError("Plan score must be between 0 and 10")
        return v

    @staticmethod
    def from_history_model(data: HistoryModel) -> 'HistoryMarketingPlan':
        """
        Convert the history model to a history marketing plan.
        """
        return HistoryMarketingPlan(
                plan_uuid=data.plan_uuid,
                plan_description=data.plan_description,
                plan_details=data.plan_details,
                budget=data.budget,
                actual_cost=data.actual_cost,
                plan_evaluation=data.plan_evaluation,
                plan_score=data.plan_score,
                created_at=data.created_at,
                evaluated_at=data.evaluated_at,
            )
    
    @staticmethod
    def extract_latest5_hist_from_db(product_name: str, product_url: str) -> List['HistoryMarketingPlan']:
        """
        Extract the latest 5 history marketing plans from the database.
        """
        q_res: List[HistoryModel] = IthacaDB.advanced_query(
            HistoryModel,
            filters={
                    "product_name": product_name, 
                    "product_url": product_url,
                    "plan_score": {"!=": None},
                    "evaluated_at": {"!=": None},
                },
            order_by="created_at",
            order_desc=True,
            limit=5
        )
        if q_res:
            return [HistoryMarketingPlan.from_history_model(res) for res in q_res]
        else:
            return []

# Holistic agent
class HolisticInput(BaseModel):
    """
    Input of holistic agent
    """
    total_budget: Optional[float] = Field(description="Total budget in USD for the marketing plans")
    product_name: str = Field(description="Name of the product being marketed")
    product_url: str = Field(description="URL of the product or company website")
    product_picture: Optional[str] = Field(description="Product picture url or data")
    marketing_history: Optional[List[HistoryMarketingPlan]] = Field(description="Marketing history of the product", default=None)


class HolisticOutput(BaseModel):
    """
    Output schema for the holistic agent.
    """
    product_name: str = Field(description="Name of the product being marketed")
    product_url: str = Field(description="URL of the product or company website")
    marketing_plan: MarketingPlan = Field(description="Marketing plan for the product")
    total_budget: Optional[float] = Field(description="Total budget in USD for the marketing plans")

    def save_to_db(self) -> bool:
        """
        Save the new marketing plan to the database.
        """
        self.marketing_plan.product_name = self.product_name
        self.marketing_plan.product_url = self.product_url
        success = IthacaDB.add(self.marketing_plan.to_history_model())
        if success:
            logger.info(f"Successfully saved marketing plan to the database")
        else:
            logger.error(f"Failed to save marketing plan to the database")


# Evaluation agent
class EvaluationInput(BaseModel):
    """
    Input of evaluation agent
    """
    product_name: str = Field(description="Name of the product being marketed")
    product_url: str = Field(description="URL of the product or company website")
    new_marketing_plans: List[MarketingPlan] = Field(description="List of new marketing plans to evaluate")
    total_budget: Optional[float] = Field(description="Total budget in USD for the new marketing plans")
    history_marketing_plans: Optional[List[HistoryMarketingPlan]] = Field(description="List of history marketing plans to compare with new marketing plans")


class EvaluationOutput(BaseModel):
    """
    Output of evaluation agent
    """
    product_name: str = Field(description="Name of the product being marketed")
    product_url: str = Field(description="URL of the product or company website")
    marketing_plan: HistoryMarketingPlan = Field(description="Marketing plan with evaluation results")

    def update_to_db(self) -> bool:
        """
        Update the evaluation output to the history table.
        """
        if not self.marketing_plan.check_exist(plan_name=self.product_name, plan_url=self.product_url):
            logger.error("Marketing plan not found")
            return False
        
        history_model = self.marketing_plan.to_history_model()
        history_model.product_name = self.product_name
        history_model.product_url = self.product_url
        success = IthacaDB.update(history_model)
        if success:
            logger.info(f"Successfully updated marketing plan to the database")
        else:
            logger.error(f"Failed to update marketing plan to the database")
        return success