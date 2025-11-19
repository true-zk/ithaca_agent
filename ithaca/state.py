from typing import Annotated, Sequence, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """
    Shared state for all agents in current workflow.
    """
    messages: Annotated[Sequence[BaseMessage], add_messages]
    number_of_steps: int