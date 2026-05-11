import docker
import requests
import logger_utils
import re
import json

logger = logger_utils.get_logger("tools", subdir="tools")
docker_client = docker.from_env()

def python_sandbox(code: str) -> str:
    """直接在 Docker 容器內執行 Code，不產生本地檔案"""
    logger.info(f"Executing Python Sandbox...")
    try:
        # 使用 sh -c 來執行 python 並從 stdin 讀取代碼
        container = docker_client.containers.run(
            image="ai-sandbox",
            command=['python3', '-c', code], # 直接作為參數傳入，或透過 stdin
            network_mode="bridge",
            mem_limit="256m",
            cpu_quota=50000,
            remove=True,
            stdout=True, stderr=True,
            detach=False
        )
        logger.info(f"Code result: {container.decode('utf-8')}")
        return container.decode('utf-8')
    except Exception as e:
        logger.error(f"Sandbox Error: {e}")
        return f"Execution Error: {str(e)}"

def web_search(url: str, params=None) -> str:
    """通用網頁抓取：支援 JSON API 和純文字/HTML 頁面"""
    logger.info(f"Fetching: {url}")
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
        }
        response = requests.get(url, params=params, timeout=15, headers=headers)
        
        logger.info(f"Status: {response.status_code}, Content-Type: {response.headers.get('Content-Type')}")

        if not response.ok:
            return f"HTTP Error {response.status_code}: {response.text[:800]}"

        content_type = response.headers.get("Content-Type", "").lower()

        if "application/json" in content_type:
            # 是 JSON API
            data = response.json()
            return json.dumps({
                "success": True,
                "status": response.status_code,
                "data": data
            }, ensure_ascii=False, indent=2)
        else:
            # 是 HTML 或純文字頁面（例如 HKO textonly）
            text = response.text[:8000]   # 限制長度，避免 token 爆炸
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
    
def get_json_from_ai(text):
    # 先試著找最外層的完整 JSON（避免抓到嵌套或文字中的）
    match = re.search(r'(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})', text, re.DOTALL)
    if not match:
        match = re.search(r'(\[[^\[\]]*(?:\[[^\[\]]*\][^\[\]]*)*\])', text, re.DOTALL)
    if match:
        try:
            parsed = json.loads(match.group(1))
            # 額外檢查是否真的是 tool call
            if isinstance(parsed, dict) and "tool" in parsed:
                return parsed
            if isinstance(parsed, list) and parsed and isinstance(parsed[0], dict) and "tool" in parsed[0]:
                return parsed
        except:
            pass
    return None