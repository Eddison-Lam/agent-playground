from datetime import datetime

MODEL_NAME = "qwen2.5:7b"
EMBED_MODEL = "nomic-embed-text"

SYSTEM_PROMPT = '''
You are a helpful AI assistant with access to tools for real-time information and computation.

=== CORE PRINCIPLES ===

1. **Smart Tool Usage:**
   - Check current conversation first - reuse recent tool results
   - Check memories for relevant data (verify timestamps)
   - Only use tools when needed

2. **Response Style:**
   - Be concise and informative
   - After tool execution, respond naturally in plain text
   - Cite sources when applicable

=== CALCULATION RULES ===

**python_sandbox:**
- MUST use for ALL calculations (even simple ones)
- ALWAYS use print() to see results
'''


def get_system_prompt(current_time: str) -> str:
    """Get system prompt with current time context."""
    day_of_week = datetime.now().strftime('%A')
    
    return f"""{SYSTEM_PROMPT}

=== CURRENT CONTEXT ===
Current Date: {current_time.split()[0]}
Current Time: {current_time}
Day of Week: {day_of_week}
"""


def build_full_prompt(
    current_time: str, 
    memories: str = "", 
    skills_instructions: str = ""
) -> str:
    """
    Build complete system prompt with dynamic context and skills.
    
    Args:
        current_time: Current timestamp
        memories: Retrieved memories from RAG
        skills_instructions: Skill instructions to inject (from router)
        
    Returns:
        Complete system prompt with all context
    """
    day_of_week = datetime.now().strftime('%A')
    
    dynamic_part = f"""

=== CURRENT CONTEXT ===
Current Date: {current_time.split()[0]}
Current Time: {current_time}
Day of Week: {day_of_week}
"""
    
    # inject skills instructions
    if skills_instructions:
        dynamic_part += f"""

=== INJECTED SKILLS ===
{skills_instructions}
"""
    
    # inject memories
    if memories:
        dynamic_part += f"""

=== PAST MEMORIES ===
{memories}

⚠️ WARNING: These memories are from PREVIOUS conversations and may be outdated.
For time-sensitive information (weather, news), prefer recent tool results.
"""
    
    return SYSTEM_PROMPT + dynamic_part