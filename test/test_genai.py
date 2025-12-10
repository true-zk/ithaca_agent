import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from pydantic import BaseModel
from ithaca.llms.gemini import gemini_llm


# class WeatherResponse(BaseModel):
#     weather: str
#     origianl_response: str

# print(WeatherResponse.model_json_schema())


# def get_weather(location: str) -> str:
#     return f"The weather in {location} is 11w222211223."


# res = gemini_llm.generate_json(
#     model="gemini-2.5-flash",
#     prompt="What is the weather in San Francisco?",
#     schema=WeatherResponse.model_json_schema(),
#     # tools=[get_weather]
# )

# print(res)


# res = gemini_llm.generate_json(
#     model="gemini-3-pro-preview",
#     prompt="What is the weather in San Francisco?",
#     schema=WeatherResponse.model_json_schema(),
#     tools=[{"google_search": {}}]
# )

# print(res)

from ithaca.utils import get_skill_by_file_name
from ithaca.llms import gemini_llm

skill = get_skill_by_file_name("create_adsets.txt")
# print(skill)

tokens = gemini_llm.count_tokens(skill)
print(tokens)