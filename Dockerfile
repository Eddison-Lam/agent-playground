# 使用輕量級基礎鏡像
FROM python:3.10-slim

# 建立一個低權限的使用者 sandbox_user
RUN useradd -m sandbox_user

# 安裝必要的套件（如 yfinance, pandas）
RUN pip install --no-cache-dir yfinance pandas requests

# 切換到該使用者，不再使用 root
USER sandbox_user

# 設定工作目錄
WORKDIR /home/sandbox_user

# 預設指令
CMD ["python3"]