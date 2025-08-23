from flask import Flask, request, Response, jsonify
import uuid
import time
import socket
import logging
import json

# Import các module đã tách
from utils.logging_config import setup_logging
from utils.queue_manager import queue_manager
from utils.terminal_ui import terminal_ui
from utils.chat_manager import chat_manager
from services.qwen_service import qwen_service
from services.chat_service import chat_service
from models.request_state import RequestState

# Cấu hình Flask để trả về JSON đẹp
app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

# Cấu hình để chấp nhận header request rất dài
app.config['MAX_CONTENT_LENGTH'] = 2048 * 1024 * 1024  # 2GB
app.config['MAX_CONTENT_PATH'] = None
app.config['MAX_COOKIE_SIZE'] = 2048 * 1024 * 1024  # 2GB

# Tăng giới hạn cho request body
app.config['MAX_CONTENT_LENGTH'] = None  # Không giới hạn

# Cấu hình thêm để xử lý request lớn
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['TEMPLATES_AUTO_RELOAD'] = True

# Tăng giới hạn JSON serialization
import sys
sys.setrecursionlimit(10000)  # Tăng recursion limit

logger = setup_logging()

@app.route('/v1/models', methods=['GET'])
def list_models():
    """List the currently loaded models"""
    route_info = "GET /v1/models - List Models"
    logger.info(f"ROUTE: {route_info}")
    terminal_ui.update_route(route_info)
    
    models = qwen_service.get_models_from_qwen()
    response = jsonify({
        "object": "list",
        "data": models
    })
    response.headers['Content-Type'] = 'application/json'
    return response

@app.route('/v1/models/<model_id>', methods=['GET'])
def get_model(model_id):
    """Get specific model information"""
    route_info = f"GET /v1/models/{model_id} - Get Model Info"
    logger.info(f"ROUTE: {route_info}")
    terminal_ui.update_route(route_info)
    
    try:
        # Lấy thông tin model từ Qwen API
        qwen_models = qwen_service.get_models_from_qwen()
        
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
        
        logger.info(f"Model config for {model_id}: contextWindow={context_window}, reservedOutputTokenSpace={reserved_output_space}, supportsThinking={supports_thinking}")
        
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
    
    route_info = f"POST /v1/chat/completions - Chat ({model}, stream: {stream})"
    logger.info(f"ROUTE: {route_info}")
    

    terminal_ui.update_route(route_info)
    
    if stream:
        logger.info("Starting streaming response...")
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
        logger.info("Starting non-streaming response...")
        # Non-streaming response - proxy to Qwen API
        return stream_qwen_response_non_streaming_with_queue(data)

def stream_qwen_response_with_queue(data):
    """Stream response from Qwen API with queue system"""
    model = data.get('model', 'qwen3-235b-a22b')
    request_id = str(uuid.uuid4())
    
    logger.info(f"Stream function called with model: {model}, request_id: {request_id}")
    
    # Đợi cho đến khi có thể xử lý với timeout
    if not queue_manager.acquire_lock(request_id):
        yield f"data: {json.dumps({'error': 'Server busy, request timed out'})}\n\n"
        return
    
    try:
        # Tạo request state cho request này
        request_state = RequestState(request_id, model)
        
        # Xử lý request hiện tại
        for chunk in chat_service.stream_qwen_response(data, request_state):
            yield chunk
    
    except Exception as e:
        logger.error(f"Error in stream_qwen_response_with_queue: {e}")
        yield f"data: {json.dumps({'error': f'Stream error: {str(e)}'})}\n\n"
    finally:
        # Đảm bảo lock được release
        queue_manager.release_lock(request_id)

def stream_qwen_response_non_streaming_with_queue(data):
    """Non-streaming response from Qwen API with queue system"""
    model = data.get('model', 'qwen3-235b-a22b')
    request_id = str(uuid.uuid4())
    
    logger.info(f"Non-streaming function called with model: {model}, request_id: {request_id}")
    
    # Kiểm tra nếu có request đang xử lý
    with queue_manager.chat_lock:
        if queue_manager.current_processing:
            logger.info(f"Non-streaming request {request_id} waiting in queue. Queue size: {len(queue_manager.chat_queue)}")
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
            logger.info(f"Non-streaming request {request_id} starting processing")
    
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

@app.errorhandler(500)
def internal_error(error):
    """Handle internal server errors and release lock"""
    route_info = "ERROR 500 - Internal Server Error"
    logger.error(f"ROUTE: {route_info}")
    terminal_ui.update_route(route_info)
    
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
    route_info = "POST /v1/completions - Deprecated"
    logger.info(f"ROUTE: {route_info}")
    terminal_ui.update_route(route_info)
    
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
    route_info = "POST /v1/embeddings - Not Supported"
    logger.info(f"ROUTE: {route_info}")
    terminal_ui.update_route(route_info)
    
    return jsonify({
        "error": {
            "message": "Embeddings not supported in this server",
            "type": "invalid_request_error",
            "code": "not_supported"
        }
    }), 400

@app.route('/v1/test/large_request', methods=['POST'])
def test_large_request():
    """Test endpoint để kiểm tra request lớn"""
    route_info = "POST /v1/test/large_request - Test Large Request"
    logger.info(f"ROUTE: {route_info}")
    terminal_ui.update_route(route_info)
    
    try:
        # Đọc raw data
        raw_data = request.get_data()
        logger.info(f"Test large request - Raw data length: {len(raw_data)} bytes")
        
        # Parse JSON
        data = request.get_json()
        
        # Tạo response với thông tin chi tiết
        response_info = {
            "success": True,
            "raw_data_length": len(raw_data),
            "parsed_data_keys": list(data.keys()) if data else [],
            "content_length": request.content_length,
            "messages_count": len(data.get('messages', [])) if data else 0,
            "server_config": {
                "max_content_length": app.config.get('MAX_CONTENT_LENGTH'),
                "max_cookie_size": app.config.get('MAX_COOKIE_SIZE')
            }
        }
        
        # Lưu test data
        with open("test_large_request.txt", "w", encoding='utf-8') as f:
            f.write(raw_data.decode('utf-8', errors='ignore'))
        
        return jsonify(response_info)
        
    except Exception as e:
        logger.error(f"Test large request error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Lấy IP address
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    
    # Startup logs
    logger.info("Success! HTTP server listening on port 1235")
    logger.warning("Server accepting connections from the local network. Only use this if you know what you are doing!")
    logger.info("")
    logger.info("Supported endpoints:")
    logger.info(f"->\tGET  http://{local_ip}:1235/v1/models")
    logger.info(f"->\tGET  http://{local_ip}:1235/v1/models/{{model_id}}")
    logger.info(f"->\tPOST http://{local_ip}:1235/v1/chat/completions")
    logger.info(f"->\tPOST http://{local_ip}:1235/v1/completions")
    logger.info(f"->\tPOST http://{local_ip}:1235/v1/embeddings")
    logger.info("")
    logger.info("Custom server with Qwen API integration")
    logger.info("Queue system enabled - requests will be queued if server is busy")
    logger.info("Think mode support enabled - <think> and </think> tags for Qwen thinking phase")
    logger.info("Lock timeout: 2 minutes, Request timeout: 60 seconds")
    logger.info("Server started.")
    logger.info("Just-in-time model loading active.")
    
    # Khởi tạo chat_id khi server bắt đầu
    logger.info("Initializing chat session...")
    chat_id = chat_manager.initialize_chat()
    if chat_id:
        logger.info(f"Chat initialized with ID: {chat_id}")
        terminal_ui.update_chat_id(chat_id)
        terminal_ui.update_parent_id(None)  # Reset parent_id khi khởi tạo
    else:
        logger.error("Failed to initialize chat")
    
    # Bắt đầu terminal UI
    terminal_ui.start()
    
    try:
        # Cấu hình Werkzeug để chấp nhận header rất dài
        from werkzeug.serving import WSGIRequestHandler
        WSGIRequestHandler.max_requestline = 2048 * 1024 * 1024  # 2GB
        WSGIRequestHandler.max_header_size = 2048 * 1024 * 1024  # 2GB
        
        # Cấu hình thêm cho Werkzeug
        import werkzeug
        werkzeug.serving.WSGIRequestHandler.max_requestline = 2048 * 1024 * 1024
        werkzeug.serving.WSGIRequestHandler.max_header_size = 2048 * 1024 * 1024
        
        # Tắt giới hạn request size
        werkzeug.serving.WSGIRequestHandler.max_requestline = None
        werkzeug.serving.WSGIRequestHandler.max_header_size = None
        
        # Tăng buffer size cho socket
        import socket
        socket.SOMAXCONN = 1024
        
        # Tăng buffer size cho request
        import os
        os.environ['FLASK_MAX_CONTENT_LENGTH'] = str(2048 * 1024 * 1024)  # 2GB
        os.environ['FLASK_MAX_CONTENT_LENGTH'] = '0'  # Không giới hạn
        
        app.run(host='0.0.0.0', port=1235, debug=False, threaded=True, processes=1)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    finally:
        terminal_ui.stop()
