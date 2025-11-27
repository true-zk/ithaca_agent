"""
Random Tools.
"""
import uuid

from langchain.tools import tool


@tool
async def random_uuid() -> str:
    """
    Generate a random UUID.
    """
    return str(uuid.uuid4())