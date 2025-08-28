import json
from flask import request, jsonify


def parse_json_request():
    """Decorator to parse JSON request bodies even when Content-Type is missing."""
    def decorator(f):
        import functools

        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            try:
                if request.content_type and 'application/json' in request.content_type:
                    request.json_data = request.get_json()
                else:
                    raw_data = request.get_data(as_text=True)
                    if raw_data:
                        request.json_data = json.loads(raw_data)
                    else:
                        request.json_data = {}
            except Exception as e:
                return jsonify({"error": f"Invalid JSON: {str(e)}"}), 400
            return f(*args, **kwargs)

        return wrapper

    return decorator


