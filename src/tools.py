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
        result = container.decode('utf-8').strip()
        if not result:
            warning_msg = (
                "[Warning: Code executed successfully but produced no output. "
                "The sandbox only returns stdout. Did you forget to use print()? "
                "Please modify your code to include print() statements.]"
            )
            logger.warning("Python sandbox returned empty output")
            return warning_msg
        
        logger.info(f"Code result: {result}")
        return result
        
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
    """
    多層容錯的 JSON 提取器
    能處理：
    - 多餘的文字
    - 缺少逗號
    - 單引號代替雙引號
    - Markdown 代碼塊
    - 尾隨逗號
    """
    
    # ========== 第 1 層：清理常見問題 ==========
    
    # 移除 Markdown 代碼塊
    text = re.sub(r'```(?:json)?\s*', '', text)
    
    # 移除前後空白
    text = text.strip()
    
    # ========== 第 2 層：直接嘗試解析 ==========
    
    try:
        parsed = json.loads(text)
        if is_valid_tool_call(parsed):
            return parsed
    except:
        pass
    
    # ========== 第 3 層：提取 JSON 區塊 ==========
    
    # 找最外層的 {} 或 []
    json_candidates = []
    
    # 方法 A: 找 { ... }
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        json_candidates.append(match.group(0))
    
    # 方法 B: 找 [ ... ]
    match = re.search(r'\[.*\]', text, re.DOTALL)
    if match:
        json_candidates.append(match.group(0))
    
    # ========== 第 4 層：修復常見錯誤 ==========
    
    for candidate in json_candidates:
        # 嘗試直接解析
        try:
            parsed = json.loads(candidate)
            if is_valid_tool_call(parsed):
                return parsed
        except:
            pass
        
        # 修復單引號問題
        fixed = candidate.replace("'", '"')
        try:
            parsed = json.loads(fixed)
            if is_valid_tool_call(parsed):
                return parsed
        except:
            pass
        
        # 修復尾隨逗號 (trailing commas)
        fixed = re.sub(r',\s*}', '}', candidate)
        fixed = re.sub(r',\s*]', ']', fixed)
        try:
            parsed = json.loads(fixed)
            if is_valid_tool_call(parsed):
                return parsed
        except:
            pass
        
        # 同時修復單引號 + 尾隨逗號
        fixed = candidate.replace("'", '"')
        fixed = re.sub(r',\s*}', '}', fixed)
        fixed = re.sub(r',\s*]', ']', fixed)
        try:
            parsed = json.loads(fixed)
            if is_valid_tool_call(parsed):
                return parsed
        except:
            pass
    
    # ========== 第 5 層：暴力逐字符匹配 ==========
    
    for start_char, end_char in [('{', '}'), ('[', ']')]:
        extracted = extract_balanced_brackets(text, start_char, end_char)
        if extracted:
            try:
                parsed = json.loads(extracted)
                if is_valid_tool_call(parsed):
                    return parsed
            except:
                pass
    
    return None


def is_valid_tool_call(parsed):
    """檢查是否為有效的 tool call"""
    if isinstance(parsed, dict) and "tool" in parsed:
        return True
    if isinstance(parsed, list) and len(parsed) > 0:
        if isinstance(parsed[0], dict) and "tool" in parsed[0]:
            return True
    return False


def extract_balanced_brackets(text, open_char, close_char):
    """用堆疊提取平衡的括號內容"""
    start_idx = text.find(open_char)
    if start_idx == -1:
        return None
    
    stack = []
    for i in range(start_idx, len(text)):
        ch = text[i]
        if ch == open_char:
            stack.append(ch)
        elif ch == close_char:
            stack.pop()
            if not stack:
                return text[start_idx:i+1]
    
    return None