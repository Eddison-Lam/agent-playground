"""Router agent for skill selection."""
import os
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from src.logger_utils import get_logger
from src.prompts.skills import get_all_skills

logger = get_logger("RouterAgent", subdir="agent")


class RouterAgent:
    """Lightweight agent that selects applicable skills."""
    
    def __init__(self):
        """Initialize router agent with cheap LLM."""
        self.llm = self._init_router_llm()
        logger.info(f"RouterAgent initialized")
    
    def _init_router_llm(self):
        """Initialize cheap router LLM."""
        provider = os.getenv("ROUTER_LLM_PROVIDER", "ollama").lower()
        
        if provider == "ollama":
            model = os.getenv("ROUTER_LLM_MODEL", "phi")
            base_url = os.getenv("ROUTER_LLM_BASE_URL", "http://localhost:11434")
            logger.info(f"Router using Ollama: {model}")
            return ChatOllama(model=model, base_url=base_url, timeout=30)
        
        elif provider in ["openai_compatible", "openai", "deepseek", "groq"]:
            model = os.getenv("ROUTER_LLM_MODEL", "gpt-3.5-turbo")
            base_url = os.getenv("ROUTER_LLM_BASE_URL", os.getenv("LLM_BASE_URL"))
            api_key = os.getenv("ROUTER_LLM_API_KEY", os.getenv("CLOUD_API_KEY"))
            
            if not all([base_url, api_key]):
                logger.warning("Router LLM config incomplete")
                return None
            
            logger.info(f"Router using OpenAI-compatible: {model}")
            return ChatOpenAI(model=model, base_url=base_url, api_key=api_key, timeout=30)
        
        else:
            logger.warning(f"Unknown router provider: {provider}")
            return None
    
    def select_skills(self, user_input: str) -> list[str]:
        """
        Analyze user input and select applicable skills.
        
        Args:
            user_input: User's query
            
        Returns:
            List of selected skill names
        """
        if not self.llm:
            logger.warning("Router LLM not available")
            return []
        
        logger.info(f"Analyzing user input for skills: {user_input[:50]}...")
        
        # Get all skills
        all_skills = get_all_skills()
        skills_desc = "\n".join([
            f"- {skill.get_info().name}: {skill.get_info().description}"
            for skill in all_skills
        ])
        
        # Router prompt
        router_prompt = f"""You are a strict classifier. Analyze if the User Input explicitly requests the usage of any available skills.

[Available Skills]
{skills_desc}

[User Input]
"{user_input}"

[Critical Rules]
1. If the user is asking about your capabilities, asking a general question, saying hello/thank you, or talking about "tools" in general, DO NOT select any skill.
2. Only select a skill if the user is explicitly asking for that specific service
3. If no skill is an exact match, you MUST respond with a blank line (absolutely nothing).

Your response:"""
        
        try:
            response = self.llm.invoke(router_prompt)
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            # Parse response
            selected = []
            skill_names = [s.get_info().name for s in all_skills]
            
            for line in response_text.strip().split('\n'):
                line = line.strip().lower()
                if line and line in skill_names:
                    selected.append(line)
            
            logger.info(f"Router selected skills: {selected}")
            return selected
        
        except Exception as e:
            logger.warning(f"Router failed: {e}")
            return []
    
    def get_skills_instructions(self, skill_names: list[str]) -> str:
        """Get instructions for selected skills."""
        from ..prompts.skills import get_all_skills
        
        all_skills = {skill.get_info().name: skill for skill in get_all_skills()}
        
        instructions = ""
        for skill_name in skill_names:
            if skill_name in all_skills:
                instructions += f"\n{all_skills[skill_name].get_instructions()}\n"
        
        return instructions