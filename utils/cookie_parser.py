import json

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

