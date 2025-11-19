from langchain.agents import create_agent
from deepagents import create_deep_agent, CompiledSubAgent

from ithaca.llms.gemini import gemini_llm
from ithaca.tools.meta_api import get_ad_accounts


SYSTEM_PROMPT = """
You are a research agent.
You are tasked with researching user's Meta Ads information.
You will use the following tools to help you:
- get_ad_accounts: to get user's ad accounts
"""


research_agent = create_agent(
    model=gemini_llm.get_langchain_llm(),
    tools=[get_ad_accounts],
    system_prompt=SYSTEM_PROMPT
)


# compiled sub agent
research_subagent = CompiledSubAgent(
    name="research_subagent",
    description="A subagent that is tasked with researching user's Meta Ads information.",
    runnable=research_agent,
)
