import sys
from pathlib import Path
import asyncio

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# from ithaca.oauth.auth import auth_manager

# if not auth_manager.get_access_token():
#     auth_manager.authenticate(force_refresh=True)

from ithaca.agents.plan_agent import PlanAgent, PlanAgentInput
from ithaca.workflow.data_type import MetaAdsAccountInfo


def test_plan_agent():
    """Test plan agent"""
    print("=" * 60)
    print("Testing plan agent")
    print("=" * 60)
    input = PlanAgentInput(
        product_name="Taptap",
        product_url="https://www.taptap.cn/",
        picture_urls=["https://play-lh.googleusercontent.com/k8vYThDw5A8sAbAVHQ1yUmO9UWCwrKDf3ggTxa4Pve8rRFquhU0a5hCFqalGTEoVKQ=w240-h480-rw"],
        research_summary="Taptap is a platform for game developers to publish their games and for users to download and play them.",
        account_info=MetaAdsAccountInfo(
            account_id="act_368401904774563",
            account_name="Tap Booster",
            amount_spent=12292.0,
            balance=0.0,
            currency="CNY",
            timezone_name="Asia/Shanghai",
            dsa_required=False,
            dsa_compliance_note="This account is not subject to European DSA requirements",
            page_id="101519255589335",
            page_name="Tap Booster",
            page_category="电子游戏",
            page_link="https://www.facebook.com/101519255589335",
            page_picture_url="https://scontent-hkg1-2.xx.fbcdn.net/v/t39.30808-1/238069387_101520358922558_3183338895528914355_n.png?stp=cp0_dst-png_s50x50&_nc_cat=104&ccb=1-7&_nc_sid=f907e8&_nc_ohc=Bp2NilujKaIQ7kNvwGPoNiY&_nc_oc=Adla88Lnueo3mgC4qLsVQPLNZ0rvhLvwasYADY2DN6nRppeu6oWyjWkIHaZcCbQCXz0&_nc_zt=24&_nc_ht=scontent-hkg1-2.xx&edm=AJdBtusEAAAA&_nc_gid=CY427mpZaWJIxEDS-3tQMQ&_nc_tpa=Q5bMBQFy_3uMmWakT1BbVZHGQa3INV0F_3iOoi3w9d5NwUz-S1nDPL6CDqcJt2MIbENyNAX59flMZviH&oh=00_AflgWeTN2m8zu5Oy9YZn8qZzerdHnidYNglRXjg7dSAptg&oe=693C465C"
        )
    )
    agent = PlanAgent()
    # print(agent)
    res = agent.run(input)
    print(res)

test_plan_agent()