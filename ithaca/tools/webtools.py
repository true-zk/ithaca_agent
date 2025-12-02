"""
Wrap the web summary tool from google genai for langchain tools.
"""
from typing import Optional, Dict, Any, List
import json
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup

from google import genai
from google.genai import types
from langchain.tools import tool

from ithaca.llms.gemini import gemini_llm


grounding_tool = types.Tool(
    google_search=types.GoogleSearch()
)


@tool
async def web_search(query: str) -> str:
    """
    Search the web for information.
    """
    return await gemini_llm.generate(query, tools=[grounding_tool])


@tool
async def web_summary(url: str, addtional_prompt: Optional[str] = None) -> str:
    """
    Summarize the content of a web page.
    
    Args:
        url: URL of the web page to summarize
        addtional_prompt: Additional prompt to guide the summary
    """
    prompt = f"Summarize the content of the following web page: {url}"
    if addtional_prompt:
        prompt += f"\n\n{addtional_prompt}"
    return await gemini_llm.generate(prompt, tools=[{"url_context": {}}])


@tool
def fetch_pictures_from_web(url: str) -> str:
    """
    Try to fetch the product pictures from the web page.
    Success return a list of image urls or base64 encoded strings of the images.
    
    Args:
        url: URL of the web page to fetch the product picture
    """
    try:
        response = requests.get(url, timeout=10, headers={
            "User-Agent": "Mozilla/5.0"
        })
        response.raise_for_status()
    except Exception as e:
        return f"Failed to fetch product picture: {e}"

    soup = BeautifulSoup(response.text, "html.parser")

    imgs = []
    for img in soup.find_all("img"):
        src = img.get("src") or img.get("data-src") or ""
        if not src:
            continue

        full_src = urljoin(url, src)

        if any(x in full_src.lower() for x in ["logo", "placeholder", "sprite"]):
            continue

        imgs.append(full_src)

    return json.dumps(imgs, indent=2)