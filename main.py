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

# Import các module đã tách
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

# Parse command line arguments
def parse_arguments():
    """Parse command line arguments"""
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

# Cấu hình Flask để trả về JSON đẹp
app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

# Cấu hình CORS để cho phép tất cả origin
CORS(app, origins="*", supports_credentials=True)

# Cấu hình để chấp nhận header request rất dài
app.config['MAX_CONTENT_LENGTH'] = 2048 * 1024 * 1024  # 2GB
app.config['MAX_CONTENT_PATH'] = None
app.config['MAX_COOKIE_SIZE'] = 2048 * 1024 * 1024  # 2GB

# Tăng giới hạn cho request body
app.config['MAX_CONTENT_LENGTH'] = None  # Không giới hạn

# Cấu hình thêm để xử lý request lớn
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['TEMPLATES_AUTO_RELOAD'] = True

# Cấu hình để chấp nhận request không có Content-Type
app.config['JSON_AS_ASCII'] = False
app.config['JSONIFY_MIMETYPE'] = 'application/json'

# Tắt kiểm tra Content-Type cho JSON
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
app.config['JSON_SORT_KEYS'] = False

# Tăng giới hạn JSON serialization
import sys
sys.setrecursionlimit(10000)  # Tăng recursion limit

# Global variables
SERVER_MODE = None
BACKGROUND_MODE = False
args = None
HTTP_SERVER = None
HTTP_THREAD = None

# Global models cache
MODELS_CACHE = None
MODELS_CACHE_TIME = None
MODELS_CACHE_LOCK = threading.Lock()

def get_cached_qwen_models(force_refresh: bool = False):
    """Lấy danh sách models từ cache toàn cục; chỉ gọi Qwen 1 lần trừ khi refresh."""
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

# Parse arguments first
args = parse_arguments()

# Setup logging based on background mode
def setup_logging_with_background():
    """Setup logging based on background mode"""
    global BACKGROUND_MODE
    if args.background:
        BACKGROUND_MODE = True
        # Redirect all output to null in background mode
        import os
        import sys
        
        # Redirect stdout and stderr to null
        if os.name == 'nt':  # Windows
            null_device = 'NUL'
        else:  # Unix/Linux/Mac
            null_device = '/dev/null'
        
        # Open null device
        null_fd = os.open(null_device, os.O_RDWR)
        
        # Redirect stdout and stderr
        os.dup2(null_fd, sys.stdout.fileno())
        os.dup2(null_fd, sys.stderr.fileno())
        
        # Close the null device
        os.close(null_fd)
        
        # Setup minimal logging for background mode
        logging.basicConfig(
            level=logging.ERROR,  # Only log errors
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(os.devnull, mode='w'),  # Log to null
                logging.NullHandler()  # No console output
            ]
        )
        return logging.getLogger(__name__)
    else:
        # Normal logging setup
        return setup_logging()

logger = setup_logging_with_background()

def _ui_log(message: str, level: str = "info"):
    """Log ra logger và cố gắng đẩy vào GUI Logs tab nếu khả dụng."""
    try:
        # Ghi ra file/console theo level
        if level == "error":
            logger.error(message)
        elif level == "warning":
            logger.warning(message)
        else:
            logger.info(message)

        # Đẩy vào UI nếu có
        try:
            ui = getattr(ui_manager, 'current_ui', None)
            if ui and hasattr(ui, 'log'):
                ui.log(message, level=level)
        except Exception:
            pass
    except Exception:
        pass

# Embedded server control for GUI
def start_embedded(host: str, port: int):
    """Start Flask app using Werkzeug make_server in background thread."""
    global HTTP_SERVER, HTTP_THREAD
    try:
        if HTTP_SERVER is not None:
            return True
        HTTP_SERVER = make_server(host, port, app)
        import threading
        HTTP_THREAD = threading.Thread(target=HTTP_SERVER.serve_forever, daemon=True)
        HTTP_THREAD.start()
        _ui_log(f"🟢 Flask started (embedded) on {host}:{port}")
        return True
    except Exception as e:
        HTTP_SERVER = None
        HTTP_THREAD = None
        _ui_log(f"Failed to start embedded server: {e}", level="error")
        return False

def stop_embedded(timeout: float = 2.0):
    """Stop embedded Werkzeug server without exiting the process."""
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
        _ui_log("🔴 Flask stopped (embedded)")
        return True
    except Exception as e:
        _ui_log(f"Failed to stop embedded server: {e}", level="error")
        return False

# Override để bỏ qua kiểm tra Content-Type
@app.before_request
def before_request():
    """Override để xử lý request không có Content-Type"""
    # Log request cơ bản và đánh dấu thời điểm bắt đầu
    try:
        g._req_start_time = time.time()
        qs = ''
        try:
            qs = request.query_string.decode('utf-8', 'ignore')
        except Exception:
            qs = ''
        _ui_log(f"➡️  {request.method} {request.path} | ip={request.remote_addr} | qs={qs}", level="info")
    except Exception:
        pass

    if request.method == 'POST' and request.path.startswith('/api/'):
        # Nếu là POST request đến Ollama API và không có Content-Type
        if not request.content_type or 'application/json' not in request.content_type:
            # Set Content-Type để Flask không báo lỗi
            request.environ['CONTENT_TYPE'] = 'application/json'

@app.after_request
def after_request(response):
    """Log status và thời gian xử lý cho mọi request"""
    try:
        start = getattr(g, '_req_start_time', None)
        elapsed_ms = int((time.time() - start) * 1000) if start else -1
    except Exception:
        pass
    return response

@app.route('/', methods=['GET'])
def root():
    """Root endpoint"""
    route_info = "GET / - Root"
    ui_manager.update_route(route_info)
    if SERVER_MODE == "ollama":
        return "Ollama is running"
    else:
        return "LM Studio is running"

@app.route('/', methods=['OPTIONS'])
def root_options():
    """OPTIONS for root endpoint"""
    route_info = "OPTIONS / - Root"
    ui_manager.update_route(route_info)
    
    response = Response()
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

@app.route('/__shutdown', methods=['POST'])
def shutdown():
    """Shutdown server with robust fallback (works even without werkzeug handle)."""
    try:
        route_info = "POST /__shutdown - Shutdown"
        ui_manager.update_route(route_info)

        # Try werkzeug shutdown first
        func = request.environ.get('werkzeug.server.shutdown')
        if func is not None:
            try:
                func()
                return jsonify({"status": "shutting down"})
            except Exception as e:
                logger.warning(f"Werkzeug shutdown failed: {e}")

        # Fallback: hard-exit the process shortly after responding
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
    """Parse tools thành text format"""
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
                    
                    # Handle enum values
                    if 'enum' in prop_info:
                        enum_values = prop_info['enum']
                        tools_text += f"    Values: {', '.join(enum_values)}\n"
            
            tools_text += "\n"
    
    return tools_text

def _make_display_data_short(data, max_len: int = 200):
    """Tạo bản sao rút gọn data chỉ để hiển thị trong UI, không ảnh hưởng dữ liệu gốc."""
    try:
        display_data = copy.deepcopy(data) if data else {}
        # Truncate long messages for display
        if 'messages' in display_data and isinstance(display_data['messages'], list):
            for msg in display_data['messages']:
                if isinstance(msg, dict) and 'content' in msg:
                    content = msg['content']
                    if isinstance(content, str) and len(content) > max_len:
                        msg['content'] = content[:max_len] + "..."
        return display_data
    except Exception:
        # Nếu có lỗi, trả về data gốc để tránh chặn log
        return data

def parse_json_request():
    """Decorator để parse JSON request không cần Content-Type"""
    def decorator(f):
        import functools
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            try:
                if request.content_type and 'application/json' in request.content_type:
                    # Nếu có Content-Type application/json, dùng get_json()
                    request.json_data = request.get_json()
                else:
                    # Nếu không có Content-Type, parse từ raw data
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

def ask_server_mode():
    """Hỏi người dùng chọn mode server hoặc sử dụng argument"""
    global SERVER_MODE
    
    # Nếu có argument --mode, sử dụng luôn
    if args.mode:
        SERVER_MODE = args.mode
        if SERVER_MODE == "lmstudio":
            if not BACKGROUND_MODE:
                print("✅ Đã chọn LM Studio Mode - Port 1235")
            return 1235
        else:
            if not BACKGROUND_MODE:
                print("✅ Đã chọn Ollama Mode - Port 11434")
            return 11434
    
    # Nếu có argument --port, xác định mode dựa trên port
    if args.port:
        if args.port == 1235:
            SERVER_MODE = "lmstudio"
            if not BACKGROUND_MODE:
                print("✅ Đã chọn LM Studio Mode - Port 1235")
            return 1235
        elif args.port == 11434:
            SERVER_MODE = "ollama"
            if not BACKGROUND_MODE:
                print("✅ Đã chọn Ollama Mode - Port 11434")
            return 11434
        else:
            # Port tùy chỉnh, hỏi mode
            pass
    
    # Trong background mode, default to lmstudio nếu không có argument
    if BACKGROUND_MODE:
        SERVER_MODE = "lmstudio"
        return 1235
    
    # Hỏi người dùng chọn mode nếu không có argument
    print("\n" + "="*50)
    print("🤖 CUSTOM SERVER - CHỌN MODE")
    print("="*50)
    print("1. LM Studio Mode (port 1235)")
    print("2. Ollama Mode (port 11434)")
    print("="*50)
    
    while True:
        try:
            choice = input("Chọn mode (1 hoặc 2): ").strip()
            if choice == "1":
                SERVER_MODE = "lmstudio"
                print("✅ Đã chọn LM Studio Mode - Port 1235")
                return 1235
            elif choice == "2":
                SERVER_MODE = "ollama"
                print("✅ Đã chọn Ollama Mode - Port 11434")
                return 11434
            else:
                print("❌ Vui lòng chọn 1 hoặc 2")
        except KeyboardInterrupt:
            print("\n🛑 Thoát chương trình")
            sys.exit(0)

# LM Studio API Endpoints
@app.route('/v1/models', methods=['GET', 'OPTIONS'])
def list_models():
    """List the currently loaded models"""
    if request.method == 'OPTIONS':
        route_info = "OPTIONS /v1/models - List Models"
        ui_manager.update_route(route_info)
        
        response = Response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response
    
    route_info = "GET /v1/models - List Models"
    ui_manager.update_route(route_info)
    
    models = get_cached_qwen_models()
    
    if SERVER_MODE == "ollama":
        # Convert to Ollama format
        formatted_models = []
        for model in models:
            model_id = model.get('id', '')
            if model_id:
                # Add :latest suffix for Ollama format
                model_name_with_latest = f"{model_id}:latest"
                formatted_models.append({
                    "id": model_name_with_latest,
                    "object": "model",
                    "created": int(time.time()),
                    "owned_by": "library"
                })
    else:
        # LM Studio format - use original models data
        formatted_models = models
    
    response = jsonify({
        "object": "list",
        "data": formatted_models
    })
    response.headers['Content-Type'] = 'application/json'
    return response



@app.route('/v1/models/<model_id>', methods=['GET'])
def get_model(model_id):
    """Get specific model information"""
    if SERVER_MODE != "lmstudio":
        return jsonify({"error": "Endpoint not available in current mode"}), 404
        
    route_info = f"GET /v1/models/{model_id} - Get Model Info"
    ui_manager.update_route(route_info)
    
    try:
        # Lấy thông tin model từ Qwen API
        qwen_models = get_cached_qwen_models()
        
        # Tìm model cụ thể
        target_model = None
        for model in qwen_models:
            if model.get('id') == model_id:
                target_model = model
                break
        
        if not target_model:
            # Nếu không tìm thấy, trả về lỗi
            return jsonify({
                "error": {
                    "message": f"Model {model_id} not found",
                    "type": "invalid_request_error",
                    "code": "model_not_found"
                }
            }), 404
        
        # Lấy thông tin chi tiết từ info.meta
        model_info = target_model.get('info', {})
        meta = model_info.get('meta', {})
        capabilities = meta.get('capabilities', {})
        
        # Map thông tin từ Qwen API sang LM Studio format
        context_window = meta.get('max_context_length', 131072)
        
        # Xác định reservedOutputTokenSpace
        if 'max_thinking_generation_length' in meta:
            reserved_output_space = meta.get('max_thinking_generation_length')
        elif 'max_summary_generation_length' in meta:
            reserved_output_space = meta.get('max_summary_generation_length')
        elif 'max_generation_length' in meta:
            reserved_output_space = meta.get('max_generation_length')
        else:
            reserved_output_space = 8192
        
        # Kiểm tra có hỗ trợ thinking không
        supports_thinking = capabilities.get('thinking', False) or capabilities.get('thinking_budget', False)
        
        # Map capabilities
        lm_capabilities = {
            "vision": capabilities.get('vision', False),
            "function_calling": True,  # Qwen hỗ trợ function calling
            "json_output": True,       # Qwen hỗ trợ JSON output
            "streaming": True,         # Qwen hỗ trợ streaming
            "document": capabilities.get('document', False),
            "video": capabilities.get('video', False),
            "audio": capabilities.get('audio', False),
            "citations": capabilities.get('citations', False)
        }
        
        # Tạo response cho LM Studio
        model_config = {
            "id": model_id,
            "object": "model",
            "created": int(time.time()),
            "owned_by": "qwen",
            "permission": [],
            "root": model_id,
            "parent": None,
            "contextWindow": context_window,
            "reservedOutputTokenSpace": reserved_output_space,
            "supportsSystemMessage": "system-role",
            "reasoningCapabilities": {
                "supportsReasoning": supports_thinking,
                "canTurnOffReasoning": supports_thinking,
                "canIOReasoning": supports_thinking,
                "openSourceThinkTags": [
                    "<think>",
                    "</think>"
                ] if supports_thinking else []
            },
            "capabilities": lm_capabilities,
            "pricing": {
                "prompt": 0.0001,
                "completion": 0.0002
            }
        }
                
        response = jsonify(model_config)
        response.headers['Content-Type'] = 'application/json'
        return response
        
    except Exception as e:
        logger.error(f"Error getting model info for {model_id}: {e}")
        return jsonify({
            "error": {
                "message": f"Failed to get model information: {str(e)}",
                "type": "server_error"
            }
        }), 500

@app.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    """Chat completions with streaming support"""
    data = request.get_json()
    stream = data.get('stream', False)
    model = data.get('model', 'qwen3-235b-a22b')

    # Remove :latest suffix for Ollama mode
    if SERVER_MODE == "ollama" and model.endswith(':latest'):
        model = model[:-7]  # Remove :latest
        data['model'] = model  # Update the model in data

    route_info = f"POST /v1/chat/completions - Chat ({model}, stream: {stream})"

    # Log route với bản sao rút gọn để hiển thị, không ảnh hưởng dữ liệu gốc
    ui_manager.update_route(route_info, _make_display_data_short(data))
    
    if stream:
        return Response(
            stream_qwen_response_with_queue(data),
            mimetype='text/plain',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Content-Type': 'text/event-stream'
            }
        )
    else:
        # Non-streaming response - proxy to Qwen API
        return stream_qwen_response_non_streaming_with_queue(data)

# Ollama API Endpoints
@app.route('/api/tags', methods=['GET'])
def ollama_list_models():
    """Ollama API: List models"""
    if SERVER_MODE != "ollama":
        return jsonify({"error": "Endpoint not available in current mode"}), 404
        
    route_info = "GET /api/tags - Ollama List Models"
    ui_manager.update_route(route_info)
    
    try:
        qwen_models = get_cached_qwen_models()
        
        # Convert Qwen models to Ollama format
        ollama_models = []
        for model in qwen_models:
            model_id = model.get('id', '')
            if model_id:
                # Format timestamp như Ollama
                from datetime import datetime
                modified_at = datetime.now().isoformat() + "+07:00"
                
                # Thêm suffix :latest cho model name
                model_name_with_latest = f"{model_id}:latest"
                
                ollama_models.append({
                    "name": model_name_with_latest,
                    "model": model_name_with_latest,
                    "modified_at": modified_at,
                    "size": 4661224676,  # Default size
                    "digest": "365c0bd3c000a25d28ddbf732fe1c6add414de7275464c4e4d1c3b5fcb5d8ad1",  # Default digest
                    "details": {
                        "parent_model": "",
                        "format": "gguf",
                        "family": "qwen",
                        "families": ["qwen"],
                        "parameter_size": "235B",
                        "quantization_level": "Q4_0"
                    }
                })
        
        return jsonify({"models": ollama_models})
        
    except Exception as e:
        logger.error(f"Error listing Ollama models: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/version', methods=['GET'])
def ollama_version():
    """Ollama API: Get version"""
    if SERVER_MODE != "ollama":
        return jsonify({"error": "Endpoint not available in current mode"}), 404
        
    route_info = "GET /api/version - Ollama Version"
    ui_manager.update_route(route_info)
    
    return jsonify({"version": "0.5.11"})

@app.route('/api/ps', methods=['GET'])
def ollama_list_running_models():
    """Ollama API: List running models"""
    if SERVER_MODE != "ollama":
        return jsonify({"error": "Endpoint not available in current mode"}), 404
        
    route_info = "GET /api/ps - Ollama List Running Models"
    ui_manager.update_route(route_info)
    
    try:
        # Lấy tất cả models từ Qwen API (vì tất cả đều đang chạy theo mặc định)
        qwen_models = get_cached_qwen_models()
        
        # Convert Qwen models to Ollama running format
        from datetime import datetime, timedelta
        
        running_models = []
        for model in qwen_models:
            model_id = model.get('id', '')
            if model_id:
                # Tính thời gian hết hạn (30 phút từ bây giờ)
                expires_at = (datetime.now() + timedelta(minutes=30)).isoformat() + "+07:00"
                
                # Thêm suffix :latest cho model name
                model_name_with_latest = f"{model_id}:latest"
                
                running_models.append({
                    "name": model_name_with_latest,
                    "model": model_name_with_latest,
                    "size": 6654289920,
                    "digest": "365c0bd3c000a25d28ddbf732fe1c6add414de7275464c4e4d1c3b5fcb5d8ad1",
                    "details": {
                        "parent_model": "",
                        "format": "gguf",
                        "family": "qwen",
                        "families": ["qwen"],
                        "parameter_size": "235B",
                        "quantization_level": "Q4_0"
                    },
                    "expires_at": expires_at,
                    "size_vram": 6654289920
                })
        
        return jsonify({"models": running_models})
        
    except Exception as e:
        logger.error(f"Error listing running Ollama models: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/show', methods=['POST'])
@parse_json_request()
def ollama_show_model():
    """Ollama API: Show model details"""
    if SERVER_MODE != "ollama":
        return jsonify({"error": "Endpoint not available in current mode"}), 404
        
    data = request.json_data
    model_name = data.get('name', '')
    # Bỏ suffix :latest nếu có
    if model_name.endswith(':latest'):
        model_name = model_name[:-7]
    
    route_info = f"POST /api/show - Ollama Show Model ({model_name})"
    ui_manager.update_route(route_info, data)
    
    try:
        qwen_models = get_cached_qwen_models()
        
        # Find the specific model
        target_model = None
        for model in qwen_models:
            if model.get('id') == model_name:
                target_model = model
                break
        
        if not target_model:
            return jsonify({"error": f"Model {model_name} not found"}), 404
        
        # Convert to Ollama format
        model_info = target_model.get('info', {})
        meta = model_info.get('meta', {})
        
        ollama_model_info = {
            "license": "Apache 2.0",
            "modelfile": f"FROM {model_name}",
            "parameters": str(meta.get('max_context_length', 131072)),
            "template": "{{ .Prompt }}",
            "system": "",
            "details": {
                "format": "gguf",
                "family": "qwen",
                "families": ["qwen"],
                "parameter_size": str(meta.get('max_context_length', 131072)),
                "quantization_level": "q4_0"
            }
        }
        
        return jsonify(ollama_model_info)
        
    except Exception as e:
        logger.error(f"Error showing Ollama model {model_name}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/generate', methods=['POST'])
@parse_json_request()
def ollama_generate():
    """Ollama API: Generate response"""
    if SERVER_MODE != "ollama":
        return jsonify({"error": "Endpoint not available in current mode"}), 404
        
    data = request.json_data
    model = data.get('model', 'qwen3-235b-a22b')
    prompt = data.get('prompt', '')
    stream = data.get('stream', False)
    
    # Xử lý model name có suffix :latest
    if model.endswith(':latest'):
        model = model[:-7]  # Bỏ :latest
    
    route_info = f"POST /api/generate - Ollama Generate ({model}, stream: {stream})"

    ui_manager.update_route(route_info, _make_display_data_short(data))
    
    # Convert Ollama format to OpenAI format
    openai_data = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": stream,
        "temperature": data.get('temperature', 0.7),
        "top_p": data.get('top_p', 1.0),
        "max_tokens": data.get('num_predict', 1000)
    }
    
    if stream:
        return Response(
            ollama_service.stream_ollama_response(openai_data),
            mimetype='application/json',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive'
            }
        )
    else:
        return ollama_service.stream_ollama_response_non_streaming(openai_data)

@app.route('/api/chat', methods=['POST'])
@parse_json_request()
def ollama_chat():
    """Ollama API: Chat endpoint"""
    if SERVER_MODE != "ollama":
        return jsonify({"error": "Endpoint not available in current mode"}), 404
        
    data = request.json_data
    model = data.get('model', 'qwen3-235b-a22b')
    messages = data.get('messages', [])
    # Default stream là True, chỉ khi có "stream": false thì mới là non-streaming
    stream = data.get('stream', True)
    tools = data.get('tools', [])
    
    # Xử lý model name có suffix :latest
    if model.endswith(':latest'):
        model = model[:-7]  # Bỏ :latest
    
    route_info = f"POST /api/chat - Ollama Chat ({model}, stream: {stream})"

    ui_manager.update_route(route_info, _make_display_data_short(data))
    
    # Parse tools thành text nếu có
    if tools:
        tools_text = parse_tools_to_text(tools)
        # Thêm tools text vào message cuối cùng
        if messages:
            last_message = messages[-1]
            if last_message.get('role') == 'user':
                last_message['content'] = f"{last_message['content']}\n\nAvailable tools:\n{tools_text}"
    
    # Convert Ollama chat format to OpenAI format
    openai_data = {
        "model": model,
        "messages": messages,
        "stream": stream,
        "temperature": data.get('temperature', 0.7),
        "top_p": data.get('top_p', 1.0),
        "max_tokens": data.get('num_predict', 1000)
    }
    
    if stream:
        return Response(
            ollama_service.stream_ollama_response(openai_data),
            mimetype='application/json',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive'
            }
        )
    else:
        return ollama_service.stream_ollama_response_non_streaming(openai_data)

def stream_qwen_response_with_queue(data):
    """Stream response from Qwen API with queue system"""
    model = data.get('model', 'qwen3-235b-a22b')
    request_id = str(uuid.uuid4())
        
    # Đợi cho đến khi có thể xử lý với timeout
    if not queue_manager.acquire_lock(request_id):
        yield f"data: {json.dumps({'error': 'Server busy, request timed out'})}\n\n"
        return
    
    try:
        # Tạo request state cho request này
        request_state = RequestState(request_id, model)
        
        # Update queue status: processing started, queue size from manager
        try:
            from utils.ui_manager import ui_manager as _ui
            status = queue_manager.get_status()
            _ui.update_queue_status(True, status.get('queue_size', 0))
        except Exception:
            pass

        # Xử lý request hiện tại
        for chunk in chat_service.stream_qwen_response(data, request_state):
            yield chunk
    
    except Exception as e:
        logger.error(f"Error in stream_qwen_response_with_queue: {e}")
        yield f"data: {json.dumps({'error': f'Stream error: {str(e)}'})}\n\n"
    finally:
        # Đảm bảo lock được release
        queue_manager.release_lock(request_id)
        # Update queue status: processing stopped
        try:
            from utils.ui_manager import ui_manager as _ui
            status = queue_manager.get_status()
            _ui.update_queue_status(False, status.get('queue_size', 0))
        except Exception:
            pass

def stream_qwen_response_non_streaming_with_queue(data):
    """Non-streaming response from Qwen API with queue system"""
    model = data.get('model', 'qwen3-235b-a22b')
    request_id = str(uuid.uuid4())
        
    # Kiểm tra nếu có request đang xử lý
    with queue_manager.chat_lock:
        if queue_manager.current_processing:
            return jsonify({
                "error": {
                    "message": "Server busy, please try again later",
                    "type": "server_error",
                    "code": "server_busy"
                }
            }), 503
        else:
            queue_manager.current_processing = True
            queue_manager.current_processing_start_time = time.time()
            # Update UI queue status
            try:
                from utils.ui_manager import ui_manager as _ui
                status = queue_manager.get_status()
                _ui.update_queue_status(True, status.get('queue_size', 0))
            except Exception:
                pass
    
    try:
        # Xử lý request hiện tại
        result = chat_service.stream_qwen_response_non_streaming(data)
        
        # Xử lý queue sau khi hoàn thành - đã được xử lý trong finally block
        
        return result
    
    except Exception as e:
        logger.error(f"Error in stream_qwen_response_non_streaming_with_queue: {e}")
        return jsonify({
            "error": {
                "message": f"Stream error: {str(e)}",
                "type": "server_error"
            }
        }), 500
    finally:
        # Đảm bảo lock được release
        queue_manager.release_lock(request_id)
        # Update UI queue status
        try:
            from utils.ui_manager import ui_manager as _ui
            status = queue_manager.get_status()
            _ui.update_queue_status(False, status.get('queue_size', 0))
        except Exception:
            pass



@app.errorhandler(500)
def internal_error(error):
    """Handle internal server errors and release lock"""
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

@app.route('/v1/completions', methods=['POST'])
def completions():
    """Text completions (deprecated)"""
    data = request.get_json() or {}
    route_info = "POST /v1/completions - Deprecated"
    ui_manager.update_route(route_info, data)
    
    return jsonify({
        "error": {
            "message": "This endpoint is deprecated. Use /v1/chat/completions instead.",
            "type": "invalid_request_error",
            "code": "deprecated_endpoint"
        }
    }), 400

@app.route('/v1/embeddings', methods=['POST'])
def embeddings():
    """Text embeddings"""
    data = request.get_json() or {}
    route_info = "POST /v1/embeddings - Not Supported"
    ui_manager.update_route(route_info, data)
    
    return jsonify({
        "error": {
            "message": "Embeddings not supported in this server",
            "type": "invalid_request_error",
            "code": "not_supported"
        }
    }), 400

if __name__ == '__main__':
    # Parse arguments first
    args = parse_arguments()
    
    # Set background mode if specified
    if args.background:
        BACKGROUND_MODE = True
    
    # Only GUI UI supported; exit if cannot initialize
    if not BACKGROUND_MODE:
        try:
            from utils.gui_ui import gui_ui
            if not gui_ui.is_display_available():
                logger.error("DISPLAY not available. GUI UI is required. Exiting.")
                raise SystemExit(1)

            # Set mode and port if specified in args
            if args.mode:
                port = 1235 if args.mode == "lmstudio" else 11434
                gui_ui.mode = args.mode
                gui_ui.port = port
            elif args.port:
                # Determine mode from port
                mode = "lmstudio" if args.port == 1235 else "ollama" if args.port == 11434 else None
                if mode:
                    gui_ui.mode = mode
                    gui_ui.port = args.port

            # Initialize GUI but don't start it yet
            if gui_ui.initialize():
                logger.info("GUI UI initialized successfully")

                # Register GUI with UI manager
                ui_manager.set_ui(gui_ui, 'gui')

                # Auto-start server if requested
                if args.start:
                    gui_ui._start_server()

                # Start GUI in main thread (this will block)
                gui_ui.run_main_loop()
            else:
                logger.error("Failed to initialize GUI UI. Exiting.")
                raise SystemExit(1)
        except SystemExit:
            raise
        except Exception as e:
            logger.error(f"Error initializing GUI: {e}")
            raise SystemExit(1)
