import requests
import json
# for logging
import logging
import os
from datetime import datetime

log_dir = "log"
if not os.path.exists(log_dir):os.makedirs(log_dir)
current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
log_filename = os.path.join(log_dir, f"test_search{current_time}.log")
logging.basicConfig(
    level=logging.INFO, 
    filename=log_filename, 
    encoding='utf-8',
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def web_search(url: str, params=None) -> str:
    """web search: support JSON API and plain text/HTML pages"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
        }
        response = requests.get(url, params=params, timeout=15, headers=headers)
        

        if not response.ok:
            return f"HTTP Error {response.status_code}: {response.text[:800]}"

        content_type = response.headers.get("Content-Type", "").lower()

        if "application/json" in content_type:
            # JSON API
            data = response.json()
            return json.dumps({
                "success": True,
                "status": response.status_code,
                "data": data
            }, ensure_ascii=False, indent=2)
        else:
            # HTML or plain text
            text = response.text[:8000]   # limit length to avoid token explosion
            return f"""URL: {url}
Status: {response.status_code}
Content-Type: {content_type}

--- Page Content ---
{text}
"""
    except requests.exceptions.RequestException as e:
        return f"Network error fetching {url}: {str(e)}"
    except Exception as e:
        logger.error(f"Web search error: {e}")
        return f"Failed to process {url}: {str(e)}"
print(web_search("https://www.hko.gov.hk/textonly/v2/indexc.htm"))