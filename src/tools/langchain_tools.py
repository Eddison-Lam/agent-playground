"""Convert tools to LangChain format for LangGraph."""
from langchain_core.tools import tool
from .implementations.web_search import WebSearchTool
from .implementations.python_sandbox import PythonSandboxTool
from src.settings import settings
from src.logger_utils import get_logger

logger = get_logger("LangChainTools", subdir="tools")

# Initialize tool instances
_web_search = WebSearchTool()
_python_sandbox = PythonSandboxTool()


@tool
def web_search(query_or_url: str, is_url: bool = True) -> str:
    """
    Fetch web content from URLs or search the web using Jina AI Reader/Search API.
    
    Use this tool when you need to:
    - Fetch current content from a specific URL (news, weather, documentation, etc.)
    - Search the web for real-time information
    - Get fresh data that might be outdated in memories
    
    For Hong Kong weather specifically, use these URLs:
    - Current weather: https://www.hko.gov.hk/textonly/v2/forecast/englishwx2.htm
    - 9-day forecast: https://www.hko.gov.hk/textonly/v2/forecast/nday_v2.htm
    - Local forecast: https://www.hko.gov.hk/textonly/v2/forecast/localc.htm
    
    Args:
        query_or_url: The URL to fetch (e.g., "https://example.com") or search query (e.g., "latest AI news")
        is_url: Set to True for fetching URLs (default), False for web search queries
        
    Returns:
        Web content in markdown format, or search results
        
    Examples:
        - Fetch a webpage: web_search("https://www.hko.gov.hk/textonly/v2/forecast/englishwx2.htm", True)
        - Search the web: web_search("Python 3.13 release notes", False)
    """
    return _web_search.execute(query_or_url=query_or_url, is_url=is_url)


@tool
def python_sandbox(code: str) -> str:
    """
    Execute Python code in a secure, isolated Docker sandbox environment.
    
    **CRITICAL: This tool ONLY returns stdout and stderr output.**
    You MUST use print() statements to see any results. Simply evaluating an expression or 
    assigning to a variable without printing will return empty output.
    
    Use this tool for:
    - ANY mathematical calculations (even simple ones like 2+2, 15*23)
    - Data processing and analysis
    - Date/time calculations
    - String manipulations
    - Statistical computations
    - Testing code logic
    - Any task requiring precise computation
    
    Args:
        code: Python code to execute. Must include print() statements to see output.
        
    Returns:
        The stdout and stderr output from your code execution
        
    Examples:
        ✅ CORRECT:
        - python_sandbox("print(2 + 2)")  → Returns "4"
        - python_sandbox("result = 15 * 23\\nprint(result)")  → Returns "345"
        - python_sandbox("import math\\nprint(math.sqrt(144))")  → Returns "12.0"
        
        ❌ WRONG (will return empty/warning):
        - python_sandbox("2 + 2")  → No output
        - python_sandbox("result = 15 * 23")  → No output
        - python_sandbox("x = 5")  → No output
        
    Important notes:
    - Always use print() to display results
    - You can use standard library modules (math, datetime, json, etc.)
    - Execution timeout: 30 seconds
    - Memory limit: 256MB
    - No network access (isolated environment)
    """
    return _python_sandbox.execute(code=code)


# Tool registry: map tool name to tool function
_TOOL_REGISTRY = {
    "web_search": web_search,
    "python_sandbox": python_sandbox,
}


def get_langchain_tools() -> list:
    """
    Get list of currently ENABLED LangChain tools.
    
    This function checks the settings to determine which tools are enabled
    and returns only those tools. This allows dynamic tool availability
    based on user settings (/setting command).
    
    Returns:
        List of enabled tool functions for LangGraph
    """
    enabled_tools = []
    
    for tool_name, tool_func in _TOOL_REGISTRY.items():
        if settings.is_enabled(tool_name):
            enabled_tools.append(tool_func)
            logger.debug(f"Tool enabled: {tool_name}")
        else:
            logger.debug(f"Tool disabled: {tool_name}")
    
    logger.info(f"Returning {len(enabled_tools)} enabled tools: {[t.name for t in enabled_tools]}")
    return enabled_tools


def get_all_tools() -> list:
    """
    Get ALL available tools regardless of enabled status.
    Useful for testing or displaying all tools.
    
    Returns:
        List of all tool functions
    """
    return list(_TOOL_REGISTRY.values())