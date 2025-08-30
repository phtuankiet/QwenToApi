import json
import os

def parse_cookie_items(cookie_list):
    cookie_pairs = []
    bearer_token = None
    for item in cookie_list:
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        value = item.get("value")
        if not name or value is None:
            continue
        cookie_pairs.append(f"{name}={value}")
        if name in ("token", "__Secure-next-auth.session-token") and isinstance(value, str) and value:
            bearer_token = value
    cookie_header = "; ".join(cookie_pairs) if cookie_pairs else None
    return cookie_header, bearer_token

def coerce_cookie_list(cookie_raw):
    if cookie_raw is None:
        return None
    if isinstance(cookie_raw, str):
        text = cookie_raw.strip()
        try:
            return json.loads(text)
        except Exception:
            return None
    if isinstance(cookie_raw, list):
        return cookie_raw
    return None

def load_cookies_from_env():
    cookies_env = os.environ.get('QWEN_COOKIES')
    if cookies_env:
        try:
            return json.loads(cookies_env)
        except Exception:
            return None
    return None

def build_header(base_headers: dict, cookie_raw: str | None = None):
    headers = dict(base_headers or {})
    
    if cookie_raw is None:
        cookie_raw = load_cookies_from_env()
    
    if cookie_raw is None:
        try:
            if os.path.exists("ui_settings.json"):
                with open("ui_settings.json", "r", encoding="utf-8") as f:
                    cookie_raw = (json.load(f) or {}).get("cookie")
        except Exception:
            cookie_raw = None

    cookie_list = coerce_cookie_list(cookie_raw)
    if not cookie_list:
        return headers
    cookie_header, token = parse_cookie_items(cookie_list)
    if cookie_header:
        headers["Cookie"] = cookie_header
    if token:
        headers["authorization"] = f"Bearer {token}"
    return headers

