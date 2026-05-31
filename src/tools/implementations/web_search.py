"""Web search and content fetching tool using Jina AI."""
import os
import requests
from typing import Optional
from ..base import BaseTool, ToolInfo
from logger_utils import get_logger
from dotenv import load_dotenv

load_dotenv()


class WebSearchTool(BaseTool):
    """
    Fetch webpage content or search the web using Jina AI Reader/Search API.
    
    Features:
    - Graceful fallback from API to free tier
    - Markdown formatted content
    - JSON search results
    """
    
    def __init__(self):
        """Initialize WebSearchTool."""
        info = ToolInfo(
            name="web_search",
            description="Fetch web content from URLs or search the web using Jina AI. Supports graceful fallback when quota exceeded.",
            enabled=True,
            needs_confirmation=False,
            timeout=30
        )
        super().__init__(info)
        self.jina_api_key = os.getenv("JINA_API_KEY", "").strip()
        self.logger.info(f"WebSearchTool initialized. API key {'available' if self.jina_api_key else 'not configured'}")
    
    def validate_arguments(self, **kwargs) -> tuple[bool, str]:
        """
        Validate web_search arguments.
        
        Args:
            **kwargs: Tool arguments
            
        Returns:
            tuple[bool, str]: (is_valid, error_message)
        """
        query_or_url = kwargs.get("query_or_url")
        is_url = kwargs.get("is_url", True)
        
        if not query_or_url:
            return False, "Missing required argument: query_or_url"
        
        if not isinstance(query_or_url, str):
            return False, "query_or_url must be a string"
        
        if not isinstance(is_url, bool):
            return False, "is_url must be a boolean"
        
        if not is_url and not self.jina_api_key:
            return False, "Web search (non-URL) requires JINA_API_KEY in .env file"
        
        return True, ""
    
    def execute(self, **kwargs) -> str:
        """
        Execute web search operation.
        
        Args:
            query_or_url: URL or search query string
            is_url: True for URL fetching, False for web search
            
        Returns:
            str: Fetched content or search results
        """
        is_valid, error_msg = self.validate_arguments(**kwargs)
        if not is_valid:
            self.logger.error(f"Validation failed: {error_msg}")
            return f" {error_msg}"
        
        query_or_url = kwargs.get("query_or_url")
        is_url = kwargs.get("is_url", True)
        
        try:
            if is_url:
                self.logger.info(f"Fetching URL: {query_or_url}")
                return self._fetch_url(query_or_url)
            else:
                self.logger.info(f"Searching: {query_or_url}")
                return self._search_web(query_or_url)
        except Exception as e:
            self.logger.error(f"Execution failed: {e}")
            return f"Web search error: {str(e)}"
    
    def _fetch_url(self, url: str) -> str:
        """
        Fetch webpage using Jina Reader.
        
        Args:
            url: Target webpage URL
            
        Returns:
            Webpage content in markdown format
        """
        jina_url = f"https://r.jina.ai/{url}"
        
        # Try with API key first
        if self.jina_api_key:
            self.logger.info(f"[Jina Reader] Fetching with API: {url}")
            headers = {
                "Authorization": f"Bearer {self.jina_api_key}",
                "X-Return-Format": "markdown"
            }
            
            try:
                response = requests.get(jina_url, headers=headers, timeout=self.info.timeout)
                
                # Fallback on quota exceeded or auth failure
                if response.status_code == 429:
                    self.logger.warning("[Jina Reader] API quota exceeded, falling back to no-auth")
                    return self._fetch_url_no_auth(jina_url, url)
                
                if response.status_code == 401:
                    self.logger.warning("[Jina Reader] API key invalid, falling back to no-auth")
                    return self._fetch_url_no_auth(jina_url, url)
                
                if not response.ok:
                    error_msg = f"HTTP {response.status_code}: {response.text[:300]}"
                    self.logger.error(error_msg)
                    return error_msg
                
                self.logger.info("[Jina Reader] Success with API")
                return response.text
            
            except requests.exceptions.Timeout:
                self.logger.warning("[Jina Reader] API timeout, falling back to no-auth")
                return self._fetch_url_no_auth(jina_url, url)
            except Exception as e:
                self.logger.warning(f"[Jina Reader] API request failed: {e}, falling back to no-auth")
                return self._fetch_url_no_auth(jina_url, url)
        
        # No API key - use free tier
        else:
            self.logger.info(f"[Jina Reader] No API key, using free tier: {url}")
            return self._fetch_url_no_auth(jina_url, url)
    
    def _fetch_url_no_auth(self, jina_url: str, original_url: str) -> str:
        """
        Fetch webpage using Jina Reader free tier.
        
        Args:
            jina_url: Jina Reader API endpoint
            original_url: Original target URL
            
        Returns:
            Webpage content or error message
        """
        try:
            self.logger.info(f"[Jina Reader No-Auth] Fetching: {original_url}")
            response = requests.get(jina_url, timeout=self.info.timeout)
            
            if not response.ok:
                error_msg = f"HTTP {response.status_code}: {response.text[:300]}"
                self.logger.error(error_msg)
                return error_msg
            
            self.logger.info("[Jina Reader No-Auth] Success")
            return response.text
        
        except requests.exceptions.Timeout:
            error_msg = f"Timeout fetching {original_url}"
            self.logger.error(error_msg)
            return error_msg
        
        except Exception as e:
            error_msg = f"Failed to fetch {original_url}: {str(e)}"
            self.logger.error(error_msg)
            return error_msg
    
    def _search_web(self, query: str) -> str:
        """
        Search the web using Jina Search API.
        
        Args:
            query: Search query string
            
        Returns:
            Search results as JSON or error message
        """
        if not self.jina_api_key:
            error_msg = "Web search requires JINA_API_KEY in .env file"
            self.logger.error(error_msg)
            return error_msg
        
        try:
            self.logger.info(f"[Jina Search] Executing search: {query}")
            
            headers = {
                "Authorization": f"Bearer {self.jina_api_key}",
                "Accept": "application/json"
            }
            
            response = requests.get(
                "https://s.jina.ai/",
                headers=headers,
                params={"q": query},
                timeout=self.info.timeout
            )
            
            if response.status_code == 429:
                error_msg = "API quota exceeded. Try again later or upgrade your plan."
                self.logger.error("[Jina Search] Quota exceeded")
                return error_msg
            
            if response.status_code == 401:
                error_msg = "Invalid JINA_API_KEY in .env"
                self.logger.error("[Jina Search] Authentication failed")
                return error_msg
            
            if not response.ok:
                error_msg = f"HTTP {response.status_code}: {response.text[:300]}"
                self.logger.error(error_msg)
                return error_msg
            
            self.logger.info("[Jina Search] Success")
            
            # Return JSON if applicable
            if "application/json" in response.headers.get("Content-Type", ""):
                import json
                data = response.json()
                return json.dumps(data, ensure_ascii=False, indent=2)
            else:
                return response.text
        
        except requests.exceptions.Timeout:
            error_msg = f"Timeout searching for '{query}'"
            self.logger.error(error_msg)
            return error_msg
        
        except Exception as e:
            error_msg = f"Search failed: {str(e)}"
            self.logger.error(error_msg)
            return error_msg