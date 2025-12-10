"""
Database model for history marketing plans.
It matches with the HistoryMarketingPlan in agent_types.py.
"""
from sqlmodel import SQLModel, Field, Column, String, Float, DateTime
from datetime import datetime


# History model
class HistoryModel(SQLModel, table=True):
    __tablename__ = "history"

    id: int | None = Field(default=None, primary_key=True)

    product_name: str | None = Field(default=None, sa_column=Column(String))
    product_url: str | None = Field(default=None, sa_column=Column(String))

    plan_uuid: str | None = Field(default=None, sa_column=Column(String))
    plan_description: str | None = Field(default=None, sa_column=Column(String))
    plan_details: str | None = Field(default=None, sa_column=Column(String))

    budget: float | None = Field(default=None, sa_column=Column(Float))
    actual_cost: float | None = Field(default=None, sa_column=Column(Float))

    plan_evaluation: str | None = Field(default=None, sa_column=Column(String))
    plan_score: float | None = Field(default=None, sa_column=Column(Float))

    created_at: datetime | None = Field(default=None, sa_column=Column(DateTime))
    evaluated_at: datetime | None = Field(default=None, sa_column=Column(DateTime))
