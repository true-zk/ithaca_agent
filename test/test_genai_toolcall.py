import sys
from pathlib import Path
import asyncio
import json

sys.path.insert(0, str(Path(__file__).parent.parent))

from google import genai
from google.genai import types

from ithaca.llms.gemini import gemini_llm
from ithaca.tools.meta_api.meta_ads_campaign import get_campaigns_tool
from ithaca.tools.meta_api import GOOGLE_TOOLS


SYSTEM_PROMPT = """
You are a planning and execution agent for Meta Ads marketing campaigns.
Your job is to: 
(1) design a complete, coherent marketing plan, 
(2) execute it by creating the necessary Campaigns, Ad Sets, Ads, and Creatives via the provided tools and data.
(3) return a clear summary of what was created (IDs, names, objectives, budgets, targeting) and any parts that failed.

Scope and responsibilities:
- Read the task description (e.g., goals, budget, products, audiences, timeframe, channels).
- Design a structured marketing plan that specifies:
  - Which campaigns to create (one or more), with objectives and budget strategy.
  - For each campaign, which ad sets to create (targeting, optimization, budget, schedule).
  - For each ad set, which ads to create (mapping to creatives).
  - For each ad, which creatives to create or reuse (image, text, CTA, links).
- Then execute this plan by calling the Meta Ads API tools to actually create the objects in the correct hierarchy and order.
- Return a clear summary of what was created (IDs, names, objectives, budgets, targeting) and any parts that failed.

Meta Ads hierarchy:
- Ad Account → Campaign → Ad Set → Ad → Creative
- Ad Account → Page

Interaction rules:
- If you need some information you should ask for it.
- After you have created the marketing plan, you should return a clear summary of what was created (IDs, names, objectives, budgets, targeting).
"""


SUCCESS_HISTORY = """\n\n
Here are some success examples to help you understand the tool calls:
- create adset with args:
    "account_id": "act_368401904774563", 
    "campaign_id": "120237264080450156", 
    "adset_name": "Test Ad Set", 
    "optimization_goal": "LINK_CLICKS", 
    "billing_event": "IMPRESSIONS",
    "status": "PAUSED",
    "bid_amount": 100,
    "start_time": "2025-12-03T12:00:00-0800",
    "end_time": "2025-12-10T12:00:00-0800",
- upload ad image with args:
    "account_id": "act_368401904774563", 
    "image_url": "https://play-lh.googleusercontent.com/k8vYThDw5A8sAbAVHQ1yUmO9UWCwrKDf3ggTxa4Pve8rRFquhU0a5hCFqalGTEoVKQ=w240-h480-rw"
"""

SYSTEM_PROMPT += SUCCESS_HISTORY


PROMPT = """The product is taptap main website, 
    The webset url is https://www.taptap.cn/
    The product picture url is https://play-lh.googleusercontent.com/k8vYThDw5A8sAbAVHQ1yUmO9UWCwrKDf3ggTxa4Pve8rRFquhU0a5hCFqalGTEoVKQ=w240-h480-rw
    The total budget is 1000 USD.
    This marketing plan should be executed in 7 days.
    The ad account id is act_368401904774563.
    The page id is 101519255589335."""


def test_native_gemini_chat():
    """Test native gemini chat"""
    print("=" * 60)
    print("Testing native gemini chat")
    print("=" * 60)
    CONFIG = types.GenerateContentConfig(
        tools=GOOGLE_TOOLS,
        system_instruction=SYSTEM_PROMPT,
        temperature=0.7,
        max_output_tokens=153600,
        thinking_config=types.ThinkingConfig(
            thinking_budget=8192
        )
    )
    chatbot = gemini_llm.client.chats.create(
        model="gemini-2.5-pro",
        config=CONFIG
    )
    history = []
    while True:
        user_input = input("Enter your input: ")
        if user_input == "exit":
            break
        if user_input.lower() == "prompt":
            user_input = PROMPT
        res = chatbot.send_message(user_input)
        history.append({"role": "user", "content": user_input})
        history.append({"role": "assistant", "content": res.text})
        print(res)
        print(res.text)

    with open("history.json", "w") as f:
        json.dump(history, f, indent=2)


# test_native_gemini_chat()


# Define the function with type hints and docstring
def get_current_temperature(location: str) -> dict:
    """Gets the current temperature for a given location.

    Args:
        location: The city and state, e.g. San Francisco, CA

    Returns:
        A dictionary containing the temperature and unit.
    """
    # ... (implementation) ...
    return {"temperature": 1111111, "unit": "Celsius"}
