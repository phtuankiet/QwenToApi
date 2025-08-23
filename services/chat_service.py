import json
import time
import uuid
import requests
import logging
from models.request_state import RequestState
from services.qwen_service import qwen_service
from utils.chat_manager import chat_manager
from config import QWEN_HEADERS, QWEN_CHAT_COMPLETIONS_URL

logger = logging.getLogger(__name__)

class ChatService:
    """Service xử lý chat completions"""
    
    def __init__(self):
        pass
    
    def stream_qwen_response(self, data, request_state=None):
        """Stream response from Qwen API with think mode support
        
        Think mode: When Qwen returns phase="think", the server will:
        - Send <think> tag when think mode starts
        - Stream content normally during think mode
        - Send </think> tag when think mode ends (status="finished")
        
        Answer mode: After think mode, Qwen switches to phase="answer" for normal response
        """
        model = data.get('model', 'qwen3-235b-a22b')
        
        # Tạo request state nếu chưa có
        if request_state is None:
            request_id = str(uuid.uuid4())
            request_state = RequestState(request_id, model)
        
        logger.info(f"Stream function called with model: {model}, request_id: {request_state.request_id}")
        
        try:
            # Sử dụng chat_id hiện tại hoặc tạo mới nếu chưa có
            chat_id = chat_manager.get_current_chat_id()
            if not chat_id:
                logger.info("No current chat_id, creating new chat...")
                chat_id = chat_manager.initialize_chat(model)
                if not chat_id:
                    logger.error("Failed to create new chat")
                    yield f"data: {json.dumps({'error': 'Failed to create new chat'})}\n\n"
                    return
                logger.info(f"Created new chat with ID: {chat_id}")
            else:
                logger.info(f"Using existing chat ID: {chat_id}")
            
            # Lấy parent_id hiện tại
            parent_id = chat_manager.get_current_parent_id()
            logger.info(f"Using parent_id: {parent_id}")
            
            # Chuẩn bị request cho Qwen API
            qwen_data = qwen_service.prepare_qwen_request(data, chat_id, model, parent_id)
            
            logger.info(f"Final Qwen request with 1 message")
            
            # Gửi request đến Qwen API
            logger.info(f"Sending request to Qwen API: {QWEN_CHAT_COMPLETIONS_URL}?chat_id={chat_id}")
            logger.info(f"Request messages count: {len(qwen_data.get('messages', []))}")
            if qwen_data.get('messages'):
                logger.info(f"First message content length: {len(qwen_data['messages'][0].get('content', ''))}")
            response = requests.post(
                f"{QWEN_CHAT_COMPLETIONS_URL}?chat_id={chat_id}",
                headers=QWEN_HEADERS,
                json=qwen_data,
                stream=True,
                timeout=300  # 5 phút timeout
            )
            
            logger.info(f"Qwen API response status: {response.status_code}")
            
            # Kiểm tra response content trước khi xử lý
            try:
                # Chỉ log response headers và status, không log content vì có thể là binary/compressed            
                # Kiểm tra content-type để xử lý phù hợp
                content_type = response.headers.get('content-type', '')
                if 'application/json' in content_type:
                    try:
                        response_json = response.json()
                        logger.info(f"Qwen API JSON response: {response_json}")
                        
                        if not response_json.get('success', True):
                            error_code = response_json.get('data', {}).get('code', 'Unknown')
                            error_details = response_json.get('data', {}).get('details', 'Unknown error')
                            logger.error(f"Qwen API error: {error_code} - {error_details}")
                            
                            if error_code == "Bad_Request" and "chat is in progress" in error_details:
                                error_msg = "Chat is currently in progress. Please wait for the current request to complete."
                            else:
                                error_msg = f"Qwen API error: {error_code} - {error_details}"
                            
                            yield f"data: {json.dumps({'error': error_msg})}\n\n"
                            return
                    except json.JSONDecodeError as e:
                        logger.error(f"Error parsing JSON response: {e}")
                else:
                    logger.info(f"Qwen API response is not JSON (content-type: {content_type})")
            except Exception as e:
                logger.error(f"Error reading response content: {e}")
            
            if response.status_code == 200:
                logger.info("Starting to stream response from Qwen API...")
                chunk_count = 0
                
                # Xử lý response content dựa trên encoding
                content_encoding = response.headers.get('content-encoding', '').lower()
                logger.info(f"Response content-encoding: {content_encoding}")
                
                if content_encoding == 'br':
                    # Brotli compression - xử lý streaming từng line riêng biệt
                    try:
                        import brotli
                        logger.info("Processing Brotli compressed streaming response...")
                        
                        # Xử lý từng line streaming riêng biệt với timeout
                        start_time = time.time()
                        for line in response.iter_lines():
                            # Kiểm tra timeout mỗi 10 giây
                            if time.time() - start_time > 300:  # 5 phút timeout
                                logger.error("Stream reading timeout")
                                yield f"data: {json.dumps({'error': 'Stream reading timeout'})}\n\n"
                                return
                                
                            if line:
                                try:
                                    # Raw data đã được decompress sẵn, chỉ cần decode
                                    line_text = line.decode('utf-8')
                                    
                                    if line_text.startswith('data: '):
                                        data_content = line_text[6:]  # Bỏ 'data: '
                                        if data_content.strip():
                                            chunk_count += 1
                                            # Chuyển đổi response format để giống LM Studio
                                            try:
                                                qwen_data = json.loads(data_content)
                                                
                                                # Xử lý response.created để lấy parent_id và response_id
                                                if 'response.created' in qwen_data:
                                                    response_created = qwen_data['response.created']
                                                    parent_id = response_created.get('parent_id')
                                                    response_id = response_created.get('response_id')
                                                    if parent_id and response_id:
                                                        chat_manager.update_parent_info(parent_id, response_id)
                                                        logger.info(f"Updated parent_id: {parent_id}, response_id: {response_id}")
                                                    continue  # Bỏ qua chunk này, không gửi về client
                                                
                                                if 'choices' in qwen_data and len(qwen_data['choices']) > 0:
                                                    # Stream tất cả content như LM Studio thực sự làm
                                                    delta = qwen_data['choices'][0].get('delta', {})
                                                    finish_reason = qwen_data['choices'][0].get('finish_reason', None)
                                                    phase = delta.get('phase', None)
                                                    
                                                    # Log phase nếu có thay đổi
                                                    request_state.log_phase_change(phase)
                                                    
                                                    # Xử lý think mode
                                                    if phase == "think":
                                                        # Nếu bắt đầu think mode và chưa gửi <think> tag
                                                        if not request_state.think_started:
                                                            request_state.think_started = True
                                                            # Gửi <think> tag
                                                            openai_format = {
                                                                "id": f"chatcmpl-{uuid.uuid4().hex[:24]}",
                                                                "object": "chat.completion.chunk",
                                                                "created": int(time.time()),
                                                                "model": model,
                                                                "system_fingerprint": model,
                                                                "choices": [{
                                                                    "index": 0,
                                                                    "delta": {"content": "<think>"},
                                                                    "logprobs": None,
                                                                    "finish_reason": None
                                                                }]
                                                            }
                                                            yield f"data: {json.dumps(openai_format)}\n\n"
                                                        
                                                        # Gửi content trong think mode
                                                        if 'content' in delta:
                                                            openai_format = {
                                                                "id": f"chatcmpl-{uuid.uuid4().hex[:24]}",
                                                                "object": "chat.completion.chunk",
                                                                "created": int(time.time()),
                                                                "model": model,
                                                                "system_fingerprint": model,
                                                                "choices": [{
                                                                    "index": 0,
                                                                    "delta": {"content": delta['content']},
                                                                    "logprobs": None,
                                                                    "finish_reason": finish_reason
                                                                }]
                                                            }
                                                            yield f"data: {json.dumps(openai_format)}\n\n"
                                                        
                                                        # Nếu think mode kết thúc (status finished)
                                                        if delta.get('status') == 'finished':
                                                            # Gửi </think> tag
                                                            openai_format = {
                                                                "id": f"chatcmpl-{uuid.uuid4().hex[:24]}",
                                                                "object": "chat.completion.chunk",
                                                                "created": int(time.time()),
                                                                "model": model,
                                                                "system_fingerprint": model,
                                                                "choices": [{
                                                                    "index": 0,
                                                                    "delta": {"content": "</think>"},
                                                                    "logprobs": None,
                                                                    "finish_reason": None
                                                                }]
                                                            }
                                                            yield f"data: {json.dumps(openai_format)}\n\n"
                                                            # Reset think state
                                                            request_state.think_started = False
                                                    elif phase == "answer" or phase is None:
                                                        # Normal content (answer phase hoặc không có phase)
                                                        if 'content' in delta:
                                                            # Format giống LM Studio
                                                            openai_format = {
                                                                "id": f"chatcmpl-{uuid.uuid4().hex[:24]}",
                                                                "object": "chat.completion.chunk",
                                                                "created": int(time.time()),
                                                                "model": model,
                                                                "system_fingerprint": model,
                                                                "choices": [{
                                                                    "index": 0,
                                                                    "delta": {"content": delta['content']},
                                                                    "logprobs": None,
                                                                    "finish_reason": finish_reason
                                                                }]
                                                            }
                                                            yield f"data: {json.dumps(openai_format)}\n\n"
                                                    
                                                    # Nếu có finish_reason, gửi [DONE] message
                                                    if finish_reason:
                                                        logger.info(f"Received finish_reason: {finish_reason}, sending [DONE] and returning")
                                                        yield "data: [DONE]\n\n"
                                                        return
                                                else:
                                                    pass
                                                    # Bỏ qua các message không có choices
                                            except json.JSONDecodeError as e:
                                                logger.error(f"JSON decode error on chunk {chunk_count}: {e}")
                                                # Gửi error message format đúng
                                                error_format = {
                                                    "error": {
                                                        "message": f"Invalid JSON in response: {str(e)}",
                                                        "type": "server_error"
                                                    }
                                                }
                                                yield f"data: {json.dumps(error_format)}\n\n"
                                                return
                                            except Exception as e:
                                                logger.error(f"Error parsing chunk {chunk_count}: {e}")
                                                # Gửi error message format đúng
                                                error_format = {
                                                    "error": {
                                                        "message": f"Error processing response: {str(e)}",
                                                        "type": "server_error"
                                                    }
                                                }
                                                yield f"data: {json.dumps(error_format)}\n\n"
                                                return
                                except UnicodeDecodeError as e:
                                    logger.error(f"Unicode decode error on line: {e}")
                                    continue
                                except Exception as e:
                                    logger.error(f"Unexpected error processing line: {e}")
                                    continue
                                    
                    except ImportError:
                        logger.error("Brotli library not installed. Please install: pip install brotli")
                        yield f"data: {json.dumps({'error': 'Brotli decompression not available'})}\n\n"
                        return
                    except Exception as e:
                        logger.error(f"Error processing Brotli stream: {e}")
                        yield f"data: {json.dumps({'error': f'Stream processing error: {e}'})}\n\n"
                        return
                
                logger.info(f"Streaming completed. Total chunks: {chunk_count}")
                # Gửi [DONE] message ở cuối nếu chưa có
                logger.info("Sending final [DONE] message")
                yield "data: [DONE]\n\n"
            else:
                error_msg = f"Error from Qwen API: {response.status_code}"
                logger.error(f"Qwen API error: {response.status_code} - {response.text}")
                yield f"data: {json.dumps({'error': error_msg})}\n\n"
                
        except requests.exceptions.Timeout:
            error_msg = "Request timeout - server took too long to respond"
            logger.error("Qwen API request timeout")
            yield f"data: {json.dumps({'error': error_msg})}\n\n"
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            logger.error(f"Stream function error: {e}")
            yield f"data: {json.dumps({'error': error_msg})}\n\n"
    
    def stream_qwen_response_non_streaming(self, data):
        """Non-streaming response from Qwen API"""
        model = data.get('model', 'qwen3-235b-a22b')
        
        try:
            # Sử dụng chat_id hiện tại hoặc tạo mới nếu chưa có
            chat_id = chat_manager.get_current_chat_id()
            if not chat_id:
                logger.info("No current chat_id, creating new chat...")
                chat_id = chat_manager.initialize_chat(model)
                if not chat_id:
                    return {
                        "error": {
                            "message": "Failed to create new chat",
                            "type": "server_error"
                        }
                    }, 500
                logger.info(f"Created new chat with ID: {chat_id}")
            else:
                logger.info(f"Using existing chat ID: {chat_id}")
            
            # Lấy parent_id hiện tại
            parent_id = chat_manager.get_current_parent_id()
            logger.info(f"Using parent_id: {parent_id}")
            
            # Chuẩn bị request cho Qwen API
            qwen_data = qwen_service.prepare_qwen_request(data, chat_id, model, parent_id)
            
            # Gửi request đến Qwen API
            logger.info(f"Non-streaming request data preview: {json.dumps(qwen_data, indent=2)[:1000]}...")
            logger.info(f"Non-streaming request messages count: {len(qwen_data.get('messages', []))}")
            if qwen_data.get('messages'):
                logger.info(f"Non-streaming first message content length: {len(qwen_data['messages'][0].get('content', ''))}")
                logger.info(f"Non-streaming first message content ends with: ...{qwen_data['messages'][0].get('content', '')[-100:]}")
            
            response = requests.post(
                f"{QWEN_CHAT_COMPLETIONS_URL}?chat_id={chat_id}",
                headers=QWEN_HEADERS,
                json=qwen_data,
                timeout=300  # 5 phút timeout
            )
            
            logger.info(f"Qwen API response status: {response.status_code}")
            
            # Kiểm tra response content cho non-streaming
            try:
                
                # Kiểm tra content-type để xử lý phù hợp
                content_type = response.headers.get('content-type', '')
                if 'application/json' in content_type:
                    try:
                        response_json = response.json()
                        
                        if not response_json.get('success', True):
                            error_code = response_json.get('data', {}).get('code', 'Unknown')
                            error_details = response_json.get('data', {}).get('details', 'Unknown error')
                            logger.error(f"Qwen API error: {error_code} - {error_details}")
                            
                            if error_code == "Bad_Request" and "chat is in progress" in error_details:
                                error_msg = "Chat is currently in progress. Please wait for the current request to complete."
                            else:
                                error_msg = f"Qwen API error: {error_code} - {error_details}"
                            
                            return {
                                "error": {
                                    "message": error_msg,
                                    "type": "server_error"
                                }
                            }, 500
                    except json.JSONDecodeError as e:
                        logger.error(f"Error parsing JSON response: {e}")
                else:
                    logger.info(f"Qwen API response is not JSON (content-type: {content_type})")
            except Exception as e:
                logger.error(f"Error reading response content: {e}")
            
            if response.status_code == 200:
                qwen_response = response.json()
                
                # Xử lý response.created để lấy parent_id và response_id (cho non-streaming)
                if 'response' in qwen_response and 'created' in qwen_response['response']:
                    response_created = qwen_response['response']['created']
                    parent_id = response_created.get('parent_id')
                    response_id = response_created.get('response_id')
                    if parent_id and response_id:
                        chat_manager.update_parent_info(parent_id, response_id)
                        logger.info(f"Updated parent_id: {parent_id}, response_id: {response_id}")
                
                # Chuyển đổi response từ Qwen format sang OpenAI format
                openai_response = {
                    "id": f"chatcmpl-{uuid.uuid4()}",
                    "object": "chat.completion",
                    "created": int(time.time()),
                    "model": model,
                    "choices": [{
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": qwen_response.get('choices', [{}])[0].get('message', {}).get('content', '')
                        },
                        "finish_reason": "stop"
                    }],
                    "usage": qwen_response.get('usage', {
                        "prompt_tokens": 0,
                        "completion_tokens": 0,
                        "total_tokens": 0
                    })
                }
                return openai_response
            else:
                return {
                    "error": {
                        "message": f"Error from Qwen API: {response.status_code}",
                        "type": "server_error"
                    }
                }, 500
                
        except requests.exceptions.Timeout:
            return {
                "error": {
                    "message": "Request timeout - server took too long to respond",
                    "type": "server_error"
                }
            }, 408
        except Exception as e:
            return {
                "error": {
                    "message": f"Error: {str(e)}",
                    "type": "server_error"
                }
            }, 500

# Global chat service instance
chat_service = ChatService()
