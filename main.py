from flask import Flask, request, Response, jsonify, g
from flask_cors import CORS
import uuid
import time
import socket
import logging
import json
import os
import argparse
import sys
import copy

from utils.logging_config import setup_logging
from utils.queue_manager import queue_manager
from utils.ui_manager import ui_manager
from utils.chat_manager import chat_manager
from services.qwen_service import qwen_service
from services.chat_service import chat_service
from services.ollama_service import ollama_service
from models.request_state import RequestState
from werkzeug.serving import make_server
import threading
from controllers.lmstudio import lmstudio_bp
from controllers.ollama import ollama_bp

def parse_arguments():
    parser = argparse.ArgumentParser(description='Custom Server with Qwen API Integration')
    parser.add_argument('--background', action='store_true',
                       help='Run server in background mode (no terminal output)')
    parser.add_argument('--mode', choices=['lmstudio', 'ollama'],
                       help='Server mode (lmstudio or ollama)')
    parser.add_argument('--port', type=int,
                       help='Server port (default: 1235 for lmstudio, 11434 for ollama)')
    parser.add_argument('--host', default='0.0.0.0',
                       help='Server host (default: 0.0.0.0)')
    parser.add_argument('--start', action='store_true',
                       help='Auto-start the server')
    return parser.parse_args()

app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

CORS(app, origins="*", supports_credentials=True)

app.config['MAX_CONTENT_LENGTH'] = 2048 * 1024 * 1024
app.config['MAX_CONTENT_PATH'] = None
app.config['MAX_COOKIE_SIZE'] = 2048 * 1024 * 1024

app.config['MAX_CONTENT_LENGTH'] = None

app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['TEMPLATES_AUTO_RELOAD'] = True

app.config['JSON_AS_ASCII'] = False
app.config['JSONIFY_MIMETYPE'] = 'application/json'

app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
app.config['JSON_SORT_KEYS'] = False

app.config.update({
    'ui_manager': ui_manager,
    'qwen_service': qwen_service,
    'chat_service': chat_service,
    'ollama_service': ollama_service,
    'queue_manager': queue_manager,
    'RequestState': RequestState,
    'SERVER_MODE': None,
})

app.register_blueprint(lmstudio_bp)
app.register_blueprint(ollama_bp)

import sys
sys.setrecursionlimit(10000)

SERVER_MODE = None
BACKGROUND_MODE = False
args = None
HTTP_SERVER = None
HTTP_THREAD = None

MODELS_CACHE = None
MODELS_CACHE_TIME = None
MODELS_CACHE_LOCK = threading.Lock()

CHAT_IDS_FILE = 'chat_ids.json'
CHAT_HISTORY_FILE = 'chat_history.json'

def load_chat_ids():
    try:
        if os.path.exists(CHAT_IDS_FILE):
            with open(CHAT_IDS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    except Exception:
        return {}

def save_chat_ids(chat_ids):
    try:
        with open(CHAT_IDS_FILE, 'w', encoding='utf-8') as f:
            json.dump(chat_ids, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def load_chat_history():
    try:
        if os.path.exists(CHAT_HISTORY_FILE):
            with open(CHAT_HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    except Exception:
        return {}

def save_chat_history(chat_history):
    try:
        with open(CHAT_HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(chat_history, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def get_cached_qwen_models(force_refresh: bool = False):
    global MODELS_CACHE, MODELS_CACHE_TIME
    try:
        with MODELS_CACHE_LOCK:
            if MODELS_CACHE is None or force_refresh:
                models = qwen_service.get_models_from_qwen()
                MODELS_CACHE = models or []
                MODELS_CACHE_TIME = int(time.time())
            return MODELS_CACHE
    except Exception as e:
        logger.error(f"Error getting cached models: {e}")
        return MODELS_CACHE or []

app.config['get_cached_qwen_models'] = get_cached_qwen_models

args = parse_arguments()

def setup_logging_with_background():
    global BACKGROUND_MODE
    if args.background:
        BACKGROUND_MODE = True
        import os
        import sys
        
        if os.name == 'nt':
            null_device = 'NUL'
        else:
            null_device = '/dev/null'
        
        null_fd = os.open(null_device, os.O_RDWR)
        
        os.dup2(null_fd, sys.stdout.fileno())
        os.dup2(null_fd, sys.stderr.fileno())
        
        os.close(null_fd)
        
        logging.basicConfig(
            level=logging.ERROR,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(os.devnull, mode='w'),
                logging.NullHandler()
            ]
        )
        return logging.getLogger(__name__)
    else:
        return setup_logging()

logger = setup_logging_with_background()
app.config['logger'] = logger

def _ui_log(message: str, level: str = "info"):
    try:
        if level == "error":
            logger.error(message)
        elif level == "warning":
            logger.warning(message)
        else:
            logger.info(message)

        try:
            ui = getattr(ui_manager, 'current_ui', None)
            if ui and hasattr(ui, 'log'):
                ui.log(message, level=level)
        except Exception:
            pass
    except Exception:
        pass

def start_embedded(host: str, port: int):
    global HTTP_SERVER, HTTP_THREAD
    try:
        if HTTP_SERVER is not None:
            return True
        HTTP_SERVER = make_server(host, port, app)
        import threading
        HTTP_THREAD = threading.Thread(target=HTTP_SERVER.serve_forever, daemon=True)
        HTTP_THREAD.start()
        _ui_log(f"Flask started (embedded) on {host}:{port}")
        return True
    except Exception as e:
        HTTP_SERVER = None
        HTTP_THREAD = None
        _ui_log(f"Failed to start embedded server: {e}", level="error")
        return False

def stop_embedded(timeout: float = 2.0):
    global HTTP_SERVER, HTTP_THREAD
    try:
        srv, th = HTTP_SERVER, HTTP_THREAD
        HTTP_SERVER = None
        HTTP_THREAD = None
        if srv is not None:
            try:
                srv.shutdown()
            except Exception:
                pass
        if th is not None and th.is_alive():
            try:
                th.join(timeout)
            except Exception:
                pass
        _ui_log("Flask stopped (embedded)")
        return True
    except Exception as e:
        _ui_log(f"Failed to stop embedded server: {e}", level="error")
        return False

@app.before_request
def before_request():
    try:
        g._req_start_time = time.time()
        params_keys = ''
        try:
            args_dict = request.args.to_dict(flat=True)
            params_keys = '{' + ', '.join(args_dict.keys()) + '}' if args_dict else '{}'
        except Exception:
            params_keys = '{}'
        
        try:
            raw_body = request.get_data(as_text=True)
            body_keys = ""
            try:
                data = json.loads(raw_body)
                if isinstance(data, dict):
                    body_keys = '{' + ', '.join(data.keys()) + '}'
                elif isinstance(data, list):
                    body_keys = '{' + ', '.join(data[0].keys()) + '}' if data else ''
                else:
                    body_keys = ''
            except Exception:
                body_keys = ''
        except Exception:
            body_keys = ""
        
        _ui_log(f"{request.method} {request.path} | ip={request.remote_addr} | params={params_keys} | body={body_keys}", level="info")
    except Exception:
        pass

    try:
        ui = getattr(ui_manager, 'current_ui', None)
        if ui is not None and hasattr(ui, 'mode'):
            mode_value = getattr(ui, 'mode', None)
            if mode_value in ("ollama", "lmstudio"):
                app.config['SERVER_MODE'] = mode_value
    except Exception:
        pass

    if request.method == 'POST' and request.path.startswith('/api/'):
        if not request.content_type or 'application/json' not in request.content_type:
            request.environ['CONTENT_TYPE'] = 'application/json'

@app.after_request
def after_request(response):
    try:
        start = getattr(g, '_req_start_time', None)
        elapsed_ms = int((time.time() - start) * 1000) if start else -1
    except Exception:
        pass
    return response

@app.route('/', methods=['GET'])
def root():
    route_info = "GET / - Root"
    ui_manager.update_route(route_info)
    if SERVER_MODE == "ollama":
        return "Ollama is running"
    else:
        return "LM Studio is running"

@app.route('/', methods=['OPTIONS'])
def root_options():
    route_info = "OPTIONS / - Root"
    ui_manager.update_route(route_info)
    
    response = Response()
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

@app.route('/__shutdown', methods=['POST'])
def shutdown():
    try:
        route_info = "POST /__shutdown - Shutdown"
        ui_manager.update_route(route_info)

        func = request.environ.get('werkzeug.server.shutdown')
        if func is not None:
            try:
                func()
                return jsonify({"status": "shutting down"})
            except Exception as e:
                logger.warning(f"Werkzeug shutdown failed: {e}")

        try:
            import threading, os, time as _time
            def _delayed_exit():
                try:
                    _time.sleep(0.2)
                finally:
                    os._exit(0)
            threading.Thread(target=_delayed_exit, daemon=True).start()
            return jsonify({"status": "shutting down (fallback)"})
        except Exception as e:
            logger.error(f"Fallback shutdown failed: {e}")
            return jsonify({"error": str(e)}), 500

    except Exception as e:
        logger.error(f"Shutdown error: {e}")
        return jsonify({"error": str(e)}), 500

def parse_tools_to_text(tools):
    tools_text = ""
    for i, tool in enumerate(tools):
        if tool.get('type') == 'function':
            func = tool.get('function', {})
            name = func.get('name', '')
            description = func.get('description', '')
            parameters = func.get('parameters', {})
            
            tools_text += f"Function {i+1}: {name}\n"
            if description:
                tools_text += f"Description: {description}\n"
            
            if parameters:
                param_type = parameters.get('type', 'object')
                tools_text += f"Parameters (type: {param_type}):\n"
                
                props = parameters.get('properties', {})
                required = parameters.get('required', [])
                
                for prop_name, prop_info in props.items():
                    prop_type = prop_info.get('type', 'string')
                    prop_desc = prop_info.get('description', '')
                    is_required = prop_name in required
                    
                    tools_text += f"  - {prop_name} ({prop_type})"
                    if is_required:
                        tools_text += " [required]"
                    if prop_desc:
                        tools_text += f": {prop_desc}"
                    tools_text += "\n"
                    
                    if 'enum' in prop_info:
                        enum_values = prop_info['enum']
                        tools_text += f"    Values: {', '.join(enum_values)}\n"
            
            tools_text += "\n"
    
    return tools_text

def _make_display_data_short(data, max_len: int = 200):
    try:
        display_data = copy.deepcopy(data) if data else {}
        if 'messages' in display_data and isinstance(display_data['messages'], list):
            for msg in display_data['messages']:
                if isinstance(msg, dict) and 'content' in msg:
                    content = msg['content']
                    if isinstance(content, str) and len(content) > max_len:
                        msg['content'] = content[:max_len] + "..."
        return display_data
    except Exception:
        return data

def parse_json_request():
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

def load_cookies_from_file():
    try:
        if os.path.exists('cookies.txt'):
            with open('cookies.txt', 'r', encoding='utf-8') as f:
                cookie_content = f.read().strip()
                if cookie_content:
                    return cookie_content
        return None
    except Exception:
        return None

def select_chat_id():
    chat_ids = load_chat_ids()
    chat_history = load_chat_history()
    
    if not chat_ids:
        try:
            from services.qwen_service import qwen_service
            new_chat_id = qwen_service.create_new_chat()
            if new_chat_id:
                chat_ids['current'] = new_chat_id
                chat_history[new_chat_id] = []
                save_chat_ids(chat_ids)
                save_chat_history(chat_history)
                print(f"đã tạo chat mới từ Qwen server: {new_chat_id}")
                return new_chat_id
            else:
                print("không thể tạo chat từ Qwen server, tạo chat ID local...")
                new_chat_id = str(uuid.uuid4())
                chat_ids['current'] = new_chat_id
                chat_history[new_chat_id] = []
                save_chat_ids(chat_ids)
                save_chat_history(chat_history)
                return new_chat_id
        except Exception as e:
            print(f"lỗi khi tạo chat từ Qwen: {e}, tạo chat ID local...")
            new_chat_id = str(uuid.uuid4())
            chat_ids['current'] = new_chat_id
            chat_history[new_chat_id] = []
            save_chat_ids(chat_ids)
            save_chat_history(chat_history)
            return new_chat_id
    
    existing_chat_ids = [k for k in chat_ids.keys() if k != 'current']
    current_chat_id = chat_ids.get('current')
    
    all_chat_ids = list(chat_history.keys())
    if current_chat_id and current_chat_id not in all_chat_ids:
        all_chat_ids.append(current_chat_id)
    
    if not all_chat_ids:
        print("không có chat ID nào, tạo mới...")
        try:
            from services.qwen_service import qwen_service
            new_chat_id = qwen_service.create_new_chat()
            if new_chat_id:
                chat_ids['current'] = new_chat_id
                chat_history[new_chat_id] = []
                save_chat_ids(chat_ids)
                save_chat_history(chat_history)
                print(f"đã tạo chat mới từ Qwen server: {new_chat_id}")
                return new_chat_id
            else:
                print("không thể tạo chat từ Qwen server, tạo chat ID local...")
                new_chat_id = str(uuid.uuid4())
                chat_ids['current'] = new_chat_id
                chat_history[new_chat_id] = []
                save_chat_ids(chat_ids)
                save_chat_history(chat_history)
                return new_chat_id
        except Exception as e:
            print(f"lỗi khi tạo chat từ Qwen: {e}, tạo chat ID local...")
            new_chat_id = str(uuid.uuid4())
            chat_ids['current'] = new_chat_id
            chat_history[new_chat_id] = []
            save_chat_ids(chat_ids)
            save_chat_history(chat_history)
            return new_chat_id
    
    print("\n" + "="*50)
    print("chat id có sẵn:")
    for i, chat_id in enumerate(all_chat_ids, 1):
        message_count = len(chat_history.get(chat_id, []))
        current_marker = " (hiện tại)" if chat_id == current_chat_id else ""
        print(f"{i}. {chat_id[:8]}... ({message_count} tin nhắn){current_marker}")
    print("q. tạo chat id mới")
    print("="*50)
    
    while True:
        try:
            choice = input("chọn: ").strip()
            if choice.lower() == 'q':
                try:
                    from services.qwen_service import qwen_service
                    new_chat_id = qwen_service.create_new_chat()
                    if new_chat_id:
                        chat_ids['current'] = new_chat_id
                        chat_history[new_chat_id] = []
                        save_chat_ids(chat_ids)
                        save_chat_history(chat_history)
                        print(f"đã tạo chat mới từ Qwen server: {new_chat_id}")
                        return new_chat_id
                    else:
                        print("không thể tạo chat từ Qwen server, tạo chat ID local...")
                        new_chat_id = str(uuid.uuid4())
                        chat_ids['current'] = new_chat_id
                        chat_history[new_chat_id] = []
                        save_chat_ids(chat_ids)
                        save_chat_history(chat_history)
                        return new_chat_id
                except Exception as e:
                    print(f"lỗi khi tạo chat từ Qwen: {e}, tạo chat ID local...")
                    new_chat_id = str(uuid.uuid4())
                    chat_ids['current'] = new_chat_id
                    chat_history[new_chat_id] = []
                    save_chat_ids(chat_ids)
                    save_chat_history(chat_history)
                    return new_chat_id
            else:
                try:
                    choice_num = int(choice)
                    if 1 <= choice_num <= len(all_chat_ids):
                        selected_chat_id = all_chat_ids[choice_num - 1]
                        chat_ids['current'] = selected_chat_id
                        save_chat_ids(chat_ids)
                        print(f"đã chọn chat id: {selected_chat_id}")
                        return selected_chat_id
                    else:
                        print(f"vui lòng chọn số từ 1 đến {len(all_chat_ids)}")
                except ValueError:
                    print("vui lòng nhập số hoặc q")
        except KeyboardInterrupt:
            print("\nthoát")
            sys.exit(0)
        except EOFError:
            print("\nlỗi input, thoát")
            sys.exit(1)

def ask_server_mode():
    global SERVER_MODE
    
    if args.mode:
        SERVER_MODE = args.mode
        app.config['SERVER_MODE'] = SERVER_MODE
        if SERVER_MODE == "lmstudio":
            if not BACKGROUND_MODE:
                print("đã chọn LM Studio - port 1235")
            return 1235
        else:
            if not BACKGROUND_MODE:
                print("đã chọn Ollama - port 11434")
            return 11434
    
    if args.port:
        if args.port == 1235:
            SERVER_MODE = "lmstudio"
            app.config['SERVER_MODE'] = SERVER_MODE
            if not BACKGROUND_MODE:
                print("đã chọn LM Studio - port 1235")
            return 1235
        elif args.port == 11434:
            SERVER_MODE = "ollama"
            app.config['SERVER_MODE'] = SERVER_MODE
            if not BACKGROUND_MODE:
                print("đã chọn Ollama - port 11434")
            return 11434
        else:
            pass
    
    if BACKGROUND_MODE:
        SERVER_MODE = "lmstudio"
        app.config['SERVER_MODE'] = SERVER_MODE
        return 1235
    
    print("\n" + "="*50)
    print("chọn mode")
    print("1. ollama")
    print("2. lm studio")
    print("="*50)
    while True:
        try:
            choice = input("chọn: ").strip()
            if choice == "1":
                SERVER_MODE = "ollama"
                app.config['SERVER_MODE'] = SERVER_MODE
                print("đã chọn Ollama - port 11434")
                return 11434
            elif choice == "2":
                SERVER_MODE = "lmstudio"
                app.config['SERVER_MODE'] = SERVER_MODE
                print("đã chọn LM Studio - port 1235")
                return 1235
            else:
                print("vui lòng chọn 1 hoặc 2")
        except KeyboardInterrupt:
            print("\nthoát")
            sys.exit(0)

@app.errorhandler(500)
def internal_error(error):
    route_info = "ERROR 500 - Internal Server Error"
    logger.error(f"ROUTE: {route_info}")
    ui_manager.update_route(route_info)
    
    logger.error(f"Internal server error: {error}")
    queue_manager.release_lock("error_handler")
    return jsonify({
        "error": {
            "message": "Internal server error",
            "type": "server_error"
        }
    }), 500

if __name__ == '__main__':
    args = parse_arguments()
    if args.background:
        BACKGROUND_MODE = True
    
    cookies = load_cookies_from_file()
    if cookies:
        print("đã tải cookies từ cookies.txt")
        os.environ['QWEN_COOKIES'] = cookies
    
    chat_id = select_chat_id()
    print(f"chat id hiện tại: {chat_id}")
    
    port = ask_server_mode()
    host = args.host or '0.0.0.0'
    app.config['SERVER_MODE'] = SERVER_MODE
    app.config['CURRENT_CHAT_ID'] = chat_id
    
    if not BACKGROUND_MODE:
        print("server đang chạy")
        print(f"mode: {SERVER_MODE}")
        print(f"host: {host}")
        print(f"port: {port}")
        print(f"chat id: {chat_id}")
        print("truy cập: http://0.0.0.0:" + str(port))
    
    app.run(host=host, port=port, threaded=True)
