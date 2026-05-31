"""Utility functions for tools."""
import re
import json
from logger_utils import get_logger

logger = get_logger("ToolUtils", subdir="tools")


def extract_json(text: str) -> dict | list | None:
    """
    Multi-layer robust JSON extraction.
    Handles:
    - Extra text
    - Missing commas
    - Single quotes instead of double quotes
    - Markdown code blocks
    - Trailing commas
    
    Args:
        text: Text containing JSON
        
    Returns:
        Parsed JSON object or None if extraction fails
    """
    
    # Layer 1: Clean common issues
    text = re.sub(r'```(?:json)?\s*', '', text)
    text = text.strip()
    
    # Layer 2: Try direct parsing
    try:
        parsed = json.loads(text)
        if _is_valid_tool_call(parsed):
            logger.debug("JSON extracted via direct parsing")
            return parsed
    except:
        pass
    
    # Layer 3: Extract JSON blocks
    json_candidates = []
    
    # Method A: Find { ... }
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        json_candidates.append(match.group(0))
    
    # Method B: Find [ ... ]
    match = re.search(r'\[.*\]', text, re.DOTALL)
    if match:
        json_candidates.append(match.group(0))
    
    # Layer 4: Try to fix common errors
    for candidate in json_candidates:
        # Direct parsing
        try:
            parsed = json.loads(candidate)
            if _is_valid_tool_call(parsed):
                logger.debug("JSON extracted via direct candidate parsing")
                return parsed
        except:
            pass
        
        # Fix single quotes
        fixed = candidate.replace("'", '"')
        try:
            parsed = json.loads(fixed)
            if _is_valid_tool_call(parsed):
                logger.debug("JSON extracted via single quote fixing")
                return parsed
        except:
            pass
        
        # Fix trailing commas
        fixed = re.sub(r',\s*}', '}', candidate)
        fixed = re.sub(r',\s*]', ']', fixed)
        try:
            parsed = json.loads(fixed)
            if _is_valid_tool_call(parsed):
                logger.debug("JSON extracted via trailing comma fixing")
                return parsed
        except:
            pass
        
        # Fix both single quotes + trailing commas
        fixed = candidate.replace("'", '"')
        fixed = re.sub(r',\s*}', '}', fixed)
        fixed = re.sub(r',\s*]', ']', fixed)
        try:
            parsed = json.loads(fixed)
            if _is_valid_tool_call(parsed):
                logger.debug("JSON extracted via quote + comma fixing")
                return parsed
        except:
            pass
    
    # Layer 5: Brute force bracket extraction
    for start_char, end_char in [('{', '}'), ('[', ']')]:
        extracted = _extract_balanced_brackets(text, start_char, end_char)
        if extracted:
            try:
                parsed = json.loads(extracted)
                if _is_valid_tool_call(parsed):
                    logger.debug("JSON extracted via bracket extraction")
                    return parsed
            except:
                pass
    
    logger.warning("Failed to extract valid JSON from text")
    return None


def _is_valid_tool_call(parsed: any) -> bool:
    """
    Check if parsed data is a valid tool call.
    
    Args:
        parsed: Parsed JSON object
        
    Returns:
        True if valid tool call format
    """
    if isinstance(parsed, dict) and "tool" in parsed:
        return True
    if isinstance(parsed, list) and len(parsed) > 0:
        if isinstance(parsed[0], dict) and "tool" in parsed[0]:
            return True
    return False


def _extract_balanced_brackets(text: str, open_char: str, close_char: str) -> str | None:
    """
    Extract balanced bracket content using stack algorithm.
    
    Args:
        text: Source text
        open_char: Opening bracket character
        close_char: Closing bracket character
        
    Returns:
        Extracted bracket content or None
    """
    start_idx = text.find(open_char)
    if start_idx == -1:
        return None
    
    stack = []
    for i in range(start_idx, len(text)):
        ch = text[i]
        if ch == open_char:
            stack.append(ch)
        elif ch == close_char:
            if stack:
                stack.pop()
                if not stack:
                    return text[start_idx:i+1]
    
    return None