import uuid
x_request_id = str(uuid.uuid4())

# Cấu hình API Qwen
QWEN_API_BASE = "https://chat.qwen.ai/api"
QWEN_MODELS_URL = f"{QWEN_API_BASE}/models"
QWEN_NEW_CHAT_URL = f"{QWEN_API_BASE}/v2/chats/new"
QWEN_CHAT_COMPLETIONS_URL = f"{QWEN_API_BASE}/v2/chat/completions"

# Cookie và headers
authorization = "Bearer "
bx_ua = ""
bx_umidtoken = ""
QWEN_COOKIE = ""

QWEN_HEADERS = {
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "en-US,en;q=0.9",
    "authorization": authorization,
    "bx-ua": bx_ua,
    "bx-umidtoken": bx_umidtoken,
    "bx-v": "2.5.31",
    "Connection": "keep-alive",
    "content-type": "application/json; charset=UTF-8",
    "Cookie": QWEN_COOKIE,
    "DNT": "1",
    "Host": "chat.qwen.ai",
    "Origin": "https://chat.qwen.ai",
    "Referer": "https://chat.qwen.ai/c/guest",
    "sec-ch-ua": '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "source": "web",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
    "version": "0.0.191",
    "x-accel-buffering": "no",
    "x-request-id": x_request_id
}
