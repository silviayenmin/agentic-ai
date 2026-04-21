from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool
import os

@tool
def web_search_tool(query: str) -> str:
    """
    Search the web for up-to-date information, documentation, or coding samples using DuckDuckGo.
    Use this when you need external context or specific coding solutions.
    """
    try:
        # DuckDuckGo is free, open source, and requires no API key.
        search = DuckDuckGoSearchRun()
        return search.invoke(query)
    except Exception as e:
        return f"Search failed: {str(e)}"
