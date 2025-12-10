import sys
from pathlib import Path
import asyncio

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# from ithaca.oauth.auth import auth_manager

# if not auth_manager.get_access_token():
#     auth_manager.authenticate(force_refresh=True)

from ithaca.agents.research_agent import ResearchAgent, ResearchAgentInput


def test_research_agent():
    """Test research agent"""
    print("=" * 60)
    print("Testing research agent")
    print("=" * 60)
    input = ResearchAgentInput(
        product_name="Taptap",
        product_url="https://www.taptap.cn/",
        picture_urls=["https://play-lh.googleusercontent.com/k8vYThDw5A8sAbAVHQ1yUmO9UWCwrKDf3ggTxa4Pve8rRFquhU0a5hCFqalGTEoVKQ=w240-h480-rw"]
    )
    agent = ResearchAgent()
    print(agent)
    res = agent.run(input)
    print(res)


test_research_agent()