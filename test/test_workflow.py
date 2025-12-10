import sys
from pathlib import Path
import asyncio
import json
import time

sys.path.insert(0, str(Path(__file__).parent.parent))

from ithaca.oauth.auth import auth_manager

if not auth_manager.get_access_token():
    auth_manager.authenticate(force_refresh=True)
else:
    print(f"Using access token: {auth_manager.get_access_token()[:10]}...")

from ithaca.workflow.data_type import MarketingInitInput
from ithaca.workflow.demo_workflow import DemoWorkFlow


def test_():
    wf = DemoWorkFlow(
        marketing_input=MarketingInitInput(
            product_name="Dirichlet.ai",
            product_url="https://www.dirichlet.cn/",
            product_picture_urls=["https://assets.tapimg.com/abd/dirichlet/android-chrome-512x512.png"]
        )
    )
    print(wf)
    print("="*20)
    print(wf.user_account_info)
    print(wf.agents)
    print(wf.session)

    start_time = time.time()
    plan = wf.run()
    end_time = time.time()
    print(f"Time taken: {end_time - start_time} seconds")


test_()

