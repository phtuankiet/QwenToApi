from flask import Blueprint, jsonify, Response, request, current_app
import time
import uuid

from utils.request_utils import parse_json_request


lmstudio_bp = Blueprint('lmstudio', __name__)


def _make_display_data_short(data, max_len: int = 200):
    import copy
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


@lmstudio_bp.route('/v1/models', methods=['GET', 'OPTIONS'])
def list_models():
    app = current_app
    ui_manager = app.config['ui_manager']
    qwen_service = app.config['qwen_service']
    get_cached_qwen_models = app.config['get_cached_qwen_models']
    SERVER_MODE = app.config.get('SERVER_MODE')

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
        formatted_models = []
        for model in models:
            model_id = model.get('id', '')
            if model_id:
                model_name_with_latest = f"{model_id}:latest"
                formatted_models.append({
                    "id": model_name_with_latest,
                    "object": "model",
                    "created": int(time.time()),
                    "owned_by": "library"
                })
    else:
        formatted_models = models

    response = jsonify({
        "object": "list",
        "data": formatted_models
    })
    response.headers['Content-Type'] = 'application/json'
    return response


@lmstudio_bp.route('/v1/models/<model_id>', methods=['GET'])
def get_model(model_id):
    app = current_app
    SERVER_MODE = app.config.get('SERVER_MODE')
    if SERVER_MODE != "lmstudio":
        return jsonify({"error": "Endpoint not available in current mode"}), 404

    ui_manager = app.config['ui_manager']
    get_cached_qwen_models = app.config['get_cached_qwen_models']
    logger = app.config['logger']

    route_info = f"GET /v1/models/{model_id} - Get Model Info"
    ui_manager.update_route(route_info)

    try:
        qwen_models = get_cached_qwen_models()
        target_model = None
        for model in qwen_models:
            if model.get('id') == model_id:
                target_model = model
                break

        if not target_model:
            return jsonify({
                "error": {
                    "message": f"Model {model_id} not found",
                    "type": "invalid_request_error",
                    "code": "model_not_found"
                }
            }), 404

        model_info = target_model.get('info', {})
        meta = model_info.get('meta', {})
        capabilities = meta.get('capabilities', {})

        context_window = meta.get('max_context_length', 131072)

        if 'max_thinking_generation_length' in meta:
            reserved_output_space = meta.get('max_thinking_generation_length')
        elif 'max_summary_generation_length' in meta:
            reserved_output_space = meta.get('max_summary_generation_length')
        elif 'max_generation_length' in meta:
            reserved_output_space = meta.get('max_generation_length')
        else:
            reserved_output_space = 8192

        supports_thinking = capabilities.get('thinking', False) or capabilities.get('thinking_budget', False)

        lm_capabilities = {
            "vision": capabilities.get('vision', False),
            "function_calling": True,
            "json_output": True,
            "streaming": True,
            "document": capabilities.get('document', False),
            "video": capabilities.get('video', False),
            "audio": capabilities.get('audio', False),
            "citations": capabilities.get('citations', False)
        }

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
                "openSourceThinkTags": ["<think>", "</think>"] if supports_thinking else []
            },
            "capabilities": lm_capabilities,
            "pricing": {"prompt": 0.0001, "completion": 0.0002}
        }

        response = jsonify(model_config)
        response.headers['Content-Type'] = 'application/json'
        return response

    except Exception as e:
        logger = app.config['logger']
        logger.error(f"Error getting model info for {model_id}: {e}")
        return jsonify({
            "error": {
                "message": f"Failed to get model information: {str(e)}",
                "type": "server_error"
            }
        }), 500


@lmstudio_bp.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    app = current_app
    ui_manager = app.config['ui_manager']
    chat_service = app.config['chat_service']
    queue_manager = app.config['queue_manager']
    RequestState = app.config['RequestState']
    logger = app.config['logger']
    SERVER_MODE = app.config.get('SERVER_MODE')

    data = request.get_json()
    stream = data.get('stream', False)
    model = data.get('model', 'qwen3-235b-a22b')

    if SERVER_MODE == "ollama" and model.endswith(':latest'):
        model = model[:-7]
        data['model'] = model

    route_info = f"POST /v1/chat/completions - Chat ({model}, stream: {stream})"
    ui_manager.update_route(route_info, _make_display_data_short(data))

    def stream_qwen_response_with_queue(data):
        request_id = str(uuid.uuid4())
        if not queue_manager.acquire_lock(request_id):
            yield f"data: {{\"error\": \"Server busy, request timed out\"}}\n\n"
            return
        try:
            request_state = RequestState(request_id, model)
            try:
                status = queue_manager.get_status()
                ui_manager.update_queue_status(True, status.get('queue_size', 0))
            except Exception:
                pass
            for chunk in chat_service.stream_qwen_response(data, request_state):
                yield chunk
        except Exception as e:
            logger.error(f"Error in stream_qwen_response_with_queue: {e}")
            yield f"data: {{\"error\": \"Stream error: {str(e)}\"}}\n\n"
        finally:
            queue_manager.release_lock(request_id)
            try:
                status = queue_manager.get_status()
                ui_manager.update_queue_status(False, status.get('queue_size', 0))
            except Exception:
                pass

    def stream_qwen_response_non_streaming_with_queue(data):
        request_id = str(uuid.uuid4())
        with queue_manager.chat_lock:
            if queue_manager.current_processing:
                return jsonify({"error": {"message": "Server busy, please try again later", "type": "server_error", "code": "server_busy"}}), 503
            else:
                queue_manager.current_processing = True
                import time as _t
                queue_manager.current_processing_start_time = _t.time()
                try:
                    status = queue_manager.get_status()
                    ui_manager.update_queue_status(True, status.get('queue_size', 0))
                except Exception:
                    pass
        try:
            result = chat_service.stream_qwen_response_non_streaming(data)
            return result
        except Exception as e:
            logger.error(f"Error in stream_qwen_response_non_streaming_with_queue: {e}")
            return jsonify({"error": {"message": f"Stream error: {str(e)}", "type": "server_error"}}), 500
        finally:
            queue_manager.release_lock(request_id)
            try:
                status = queue_manager.get_status()
                ui_manager.update_queue_status(False, status.get('queue_size', 0))
            except Exception:
                pass

    if stream:
        return Response(stream_qwen_response_with_queue(data), mimetype='text/plain', headers={'Cache-Control': 'no-cache', 'Connection': 'keep-alive', 'Content-Type': 'text/event-stream'})
    else:
        return stream_qwen_response_non_streaming_with_queue(data)


