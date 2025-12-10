from typing import Dict, Any
import json

from .base import BaseAgent
from .research_agent import ResearchAgent
from .plan_agent import PlanAgent
from .update_agent import UpdateAgent
from .summary_agent import SummaryAgent
from ithaca.settings import AGENT_CONFIG_FILE


class AgentFactory:
    _mapping = {
        "research": ResearchAgent,
        "plan": PlanAgent,
        "update": UpdateAgent,
        "summary": SummaryAgent
    }

    _default_config = {
        "research": {},
        "plan": {},
        "update": {},
        "summary": {}
    }

    @classmethod
    def build_agent(cls, name: str, config: Dict[str, Any]) -> BaseAgent:
        try:
            agent = cls._mapping[name](**config)
            return agent
        except Exception as e:
            raise e
    
    @classmethod
    def build_all(cls) -> Dict[str, BaseAgent]:
        if AGENT_CONFIG_FILE and AGENT_CONFIG_FILE.endwith(".json"):
            with open(AGENT_CONFIG_FILE, "r") as f:
                config_dict = json.loads(f)
        else:
            config_dict = cls._default_config
        
        agents = {}
        for name, config in config_dict.items():
            agents[name] = cls.build_agent(name, config)
        return agents