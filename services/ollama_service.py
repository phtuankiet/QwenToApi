import json
import time
import uuid
import requests
import logging
from datetime import datetime
from models.request_state import RequestState
from services.qwen_service import qwen_service
from utils.chat_manager import chat_manager
from config import QWEN_HEADERS, QWEN_CHAT_COMPLETIONS_URL

logger = logging.getLogger(__name__)

class OllamaService:
    """Service xử lý Ollama API requests"""
    
    def __init__(self):
        pass
    
    def stream_ollama_response(self, data):
        """Stream Ollama response format - Direct Qwen API call with think mode support"""
        model = data.get('model', 'qwen3-235b-a22b')
        request_id = str(uuid.uuid4())
        request_state = RequestState(request_id, model)
        
        logger.info(f"Ollama stream function called with model: {model}, request_id: {request_id}")
        
        try:
            stream_start_ns = time.perf_counter_ns()
            first_token_ns = None
            output_token_count = 0
            input_token_count = 0
            # Ước lượng token đầu vào dựa trên số từ trong messages
            try:
                msgs = data.get('messages') or []
                if isinstance(msgs, list):
                    for m in msgs:
                        if isinstance(m, dict):
                            txt = m.get('content') or ""
                            if isinstance(txt, str):
                                input_token_count += max(1, len(txt.strip().split()))
            except Exception:
                pass
            # Tạo chat mới
            chat_id = qwen_service.create_new_chat(model)
            if not chat_id:
                logger.error("Failed to create chat for Ollama request")
                yield json.dumps({"error": "Failed to create chat"}) + "\n"
                return
            
            # Chuẩn bị request data
            qwen_data = qwen_service.prepare_qwen_request(data, chat_id, model)
            
            # Gọi Qwen API với streaming
            response = requests.post(
                f"{QWEN_CHAT_COMPLETIONS_URL}?chat_id={chat_id}",
                headers=QWEN_HEADERS,
                json=qwen_data,
                stream=True,
                timeout=300
            )
            
            # Kiểm tra response content trước khi xử lý
            try:
                content_type = response.headers.get('content-type', '')
                if 'application/json' in content_type:
                    try:
                        response_json = response.json()
                        
                        if not response_json.get('success', True):
                            error_code = response_json.get('data', {}).get('code', 'Unknown')
                            error_details = response_json.get('data', {}).get('details', 'Unknown error')
                            logger.error(f"Qwen API error: {error_code} - {error_details}")
                            
                            if error_code == "Bad_Request" and "parent_id" in error_details and "not exist" in error_details:
                                # Xử lý lỗi parent_id không tồn tại
                                logger.warning(f"Parent ID not exist error detected: {error_details}")
                                logger.info("Creating new chat and resetting parent_id...")
                                
                                # Tạo chat mới và reset parent_id
                                new_chat_id = qwen_service.create_new_chat(model)
                                if new_chat_id:
                                    logger.info(f"New chat created with ID: {new_chat_id}")
                                    # Gửi lại request với parent_id = None
                                    qwen_data = qwen_service.prepare_qwen_request(data, new_chat_id, model)
                                    
                                    logger.info(f"Retrying request with new chat_id: {new_chat_id} and parent_id: None")
                                    retry_response = requests.post(
                                        f"{QWEN_CHAT_COMPLETIONS_URL}?chat_id={new_chat_id}",
                                        headers=QWEN_HEADERS,
                                        json=qwen_data,
                                        stream=True,
                                        timeout=300
                                    )
                                    
                                    if retry_response.status_code == 200:
                                        logger.info("Retry successful, continuing with new chat...")
                                        # Tiếp tục xử lý response từ retry
                                        response = retry_response
                                    else:
                                        logger.error(f"Retry failed with status: {retry_response.status_code}")
                                        error_created_at = datetime.now().isoformat() + "Z"
                                        error_chunk = {
                                            "model": model,
                                            "created_at": error_created_at,
                                            "message": {
                                                "role": "assistant",
                                                "content": ""
                                            },
                                            "done": True,
                                            "error": f"Failed to retry with new chat: {retry_response.status_code}"
                                        }
                                        yield json.dumps(error_chunk) + "\n"
                                        return
                                else:
                                    logger.error("Failed to create new chat for retry")
                                    error_created_at = datetime.now().isoformat() + "Z"
                                    error_chunk = {
                                        "model": model,
                                        "created_at": error_created_at,
                                        "message": {
                                            "role": "assistant",
                                            "content": ""
                                        },
                                        "done": True,
                                        "error": "Failed to create new chat for retry"
                                    }
                                    yield json.dumps(error_chunk) + "\n"
                                    return
                    except json.JSONDecodeError as e:
                        logger.error(f"Error parsing JSON response: {e}")
            except Exception as e:
                logger.error(f"Error reading response content: {e}")
            
            if response.status_code == 200:
                done_sent = False
                for line in response.iter_lines():
                    if line:
                        line_str = line.decode('utf-8')
                        if line_str.startswith('data: '):
                            if first_token_ns is None:
                                first_token_ns = time.perf_counter_ns()
                            try:
                                chunk_data = json.loads(line_str[6:])
                                
                                # Xử lý response.created để lấy parent_id và response_id
                                if 'response.created' in chunk_data:
                                    response_created = chunk_data['response.created']
                                    parent_id = response_created.get('parent_id')
                                    response_id = response_created.get('response_id')
                                    if parent_id and response_id:
                                        chat_manager.update_parent_info(parent_id, response_id)
                                        logger.info(f"Updated parent_id: {parent_id}, response_id: {response_id}")
                                    continue  # Bỏ qua chunk này
                                
                                if chunk_data.get('choices') and chunk_data['choices'][0].get('delta'):
                                    delta = chunk_data['choices'][0]['delta']
                                    content = delta.get('content', '')
                                    finish_reason = chunk_data['choices'][0].get('finish_reason', None)
                                    phase = delta.get('phase', None)
                                    
                                    # Log phase nếu có thay đổi
                                    request_state.log_phase_change(phase)
                                    
                                    # Format timestamp như Ollama
                                    created_at = datetime.now().isoformat() + "Z"
                                    
                                    # Xử lý think mode
                                    if phase == "think":
                                        # Nếu bắt đầu think mode và chưa gửi thinking message
                                        if not request_state.think_started:
                                            request_state.think_started = True
                                            # Gửi thinking message với content rỗng để báo hiệu bắt đầu
                                            ollama_chunk = {
                                                "model": model,
                                                "created_at": created_at,
                                                "message": {
                                                    "role": "assistant",
                                                    "thinking": ""
                                                },
                                                "done": False
                                            }
                                            yield json.dumps(ollama_chunk) + "\n"
                                        
                                        # Gửi content trong think mode
                                        if content:
                                            ollama_chunk = {
                                                "model": model,
                                                "created_at": created_at,
                                                "message": {
                                                    "role": "assistant",
                                                    "thinking": content
                                                },
                                                "done": False
                                            }
                                            # Ước lượng token đầu ra (số từ)
                                            output_token_count += max(1, len(content.strip().split()))
                                            yield json.dumps(ollama_chunk) + "\n"
                                        
                                        # Nếu think mode kết thúc (status finished)
                                        if delta.get('status') == 'finished':
                                            # Reset think state
                                            request_state.think_started = False
                                    
                                    elif phase == "answer" or phase is None:
                                        # Normal content (answer phase hoặc không có phase)
                                        if content:
                                            ollama_chunk = {
                                                "model": model,
                                                "created_at": created_at,
                                                "message": {
                                                    "role": "assistant",
                                                    "content": content
                                                },
                                                "done": False
                                            }
                                            output_token_count += max(1, len(content.strip().split()))
                                            yield json.dumps(ollama_chunk) + "\n"
                                    
                                    # Nếu có finish_reason, gửi done message
                                    if finish_reason:
                                        final_created_at = datetime.now().isoformat() + "Z"
                                        total_duration = time.perf_counter_ns() - stream_start_ns
                                        load_duration = (first_token_ns - stream_start_ns) if first_token_ns else 0
                                        eval_duration = (time.perf_counter_ns() - first_token_ns) if first_token_ns else 0
                                        final_chunk = {
                                            "model": f"{model}:latest",
                                            "created_at": final_created_at,
                                            "message": {
                                                "role": "assistant",
                                                "content": ""
                                            },
                                            "done_reason": "stop",
                                            "done": True,
                                            "total_duration": int(total_duration),
                                            "load_duration": int(load_duration),
                                            "prompt_eval_count": int(input_token_count),
                                            "prompt_eval_duration": int(load_duration),
                                            "eval_count": int(output_token_count),
                                            "eval_duration": int(eval_duration)
                                        }
                                        yield json.dumps(final_chunk) + "\n"
                                        done_sent = True
                                        break
                                        
                            except json.JSONDecodeError:
                                continue
                        elif line_str.startswith('data: [DONE]'):
                            # Send final done message
                            final_created_at = datetime.now().isoformat() + "Z"
                            total_duration = time.perf_counter_ns() - stream_start_ns
                            load_duration = (first_token_ns - stream_start_ns) if first_token_ns else 0
                            eval_duration = (time.perf_counter_ns() - first_token_ns) if first_token_ns else 0
                            
                            final_chunk = {
                                "model": f"{model}:latest",
                                "created_at": final_created_at,
                                "message": {
                                    "role": "assistant",
                                    "content": ""
                                },
                                "done_reason": "stop",
                                "done": True,
                                "total_duration": int(total_duration),
                                "load_duration": int(load_duration),
                                "prompt_eval_count": int(input_token_count),
                                "prompt_eval_duration": int(load_duration),
                                "eval_count": int(output_token_count),
                                "eval_duration": int(eval_duration)
                            }
                            yield json.dumps(final_chunk) + "\n"
                            done_sent = True
                            break
                # Nếu vì lý do nào đó không gửi final_chunk ở trên, gửi một bản mặc định
                if not done_sent:
                    final_created_at = datetime.now().isoformat() + "Z"
                    total_duration = time.perf_counter_ns() - stream_start_ns
                    load_duration = (first_token_ns - stream_start_ns) if first_token_ns else 0
                    eval_duration = (time.perf_counter_ns() - first_token_ns) if first_token_ns else 0
                    fallback_chunk = {
                        "model": f"{model}:latest",
                        "created_at": final_created_at,
                        "message": {
                            "role": "assistant",
                            "content": ""
                        },
                        "done_reason": "stop",
                        "done": True,
                        "total_duration": int(total_duration),
                        "load_duration": int(load_duration),
                        "prompt_eval_count": int(input_token_count),
                        "prompt_eval_duration": int(load_duration),
                        "eval_count": int(output_token_count),
                        "eval_duration": int(eval_duration)
                    }
                    yield json.dumps(fallback_chunk) + "\n"
            else:
                logger.error(f"Qwen API error: {response.status_code}")
                error_created_at = datetime.now().isoformat() + "Z"
                error_chunk = {
                    "model": model,
                    "created_at": error_created_at,
                    "message": {
                        "role": "assistant",
                        "content": ""
                    },
                    "done": True,
                    "error": f"Qwen API error: {response.status_code}"
                }
                yield json.dumps(error_chunk) + "\n"
                
        except Exception as e:
            logger.error(f"Error in stream_ollama_response: {e}")
            error_created_at = datetime.now().isoformat() + "Z"
            error_chunk = {
                "model": model,
                "created_at": error_created_at,
                "message": {
                    "role": "assistant",
                    "content": ""
                },
                "done": True,
                "error": str(e)
            }
            yield json.dumps(error_chunk) + "\n"

    def call_ollama_api_direct(self, data):
        """Gọi trực tiếp Qwen API và trả về non-streaming response cho Ollama"""
        try:
            model = data.get('model', 'qwen3-235b-a22b')
            messages = data.get('messages', [])
            request_id = str(uuid.uuid4())
            request_state = RequestState(request_id, model)
            
            logger.info(f"call_ollama_api_direct called with model: {model}")
            
            # Tạo chat mới
            chat_id = qwen_service.create_new_chat(model)
            if not chat_id:
                logger.error("Failed to create chat for Ollama request")
                return {'content': 'Error: Failed to create chat'}
            
            logger.info(f"Created chat_id: {chat_id}")
            
            # Chuẩn bị request data
            qwen_data = qwen_service.prepare_qwen_request(data, chat_id, model)
            
            # Force streaming để capture content
            qwen_data['stream'] = True
            qwen_data['incremental_output'] = True
            
            logger.info(f"Prepared qwen_data with streaming: {qwen_data}")
            
            # Gọi Qwen API với streaming để capture toàn bộ content
            logger.info(f"Calling Qwen API with streaming: {QWEN_CHAT_COMPLETIONS_URL}?chat_id={chat_id}")
            response = requests.post(
                f"{QWEN_CHAT_COMPLETIONS_URL}?chat_id={chat_id}",
                headers=QWEN_HEADERS,
                json=qwen_data,
                stream=True,
                timeout=300
            )
            
            logger.info(f"Qwen API response status: {response.status_code}")
            
            # Kiểm tra response content trước khi xử lý
            try:
                content_type = response.headers.get('content-type', '')
                if 'application/json' in content_type:
                    try:
                        response_json = response.json()
                        
                        if not response_json.get('success', True):
                            error_code = response_json.get('data', {}).get('code', 'Unknown')
                            error_details = response_json.get('data', {}).get('details', 'Unknown error')
                            logger.error(f"Qwen API error: {error_code} - {error_details}")
                            
                            if error_code == "Bad_Request" and "parent_id" in error_details and "not exist" in error_details:
                                # Xử lý lỗi parent_id không tồn tại
                                logger.warning(f"Parent ID not exist error detected: {error_details}")
                                logger.info("Creating new chat and resetting parent_id...")
                                
                                # Tạo chat mới và reset parent_id
                                new_chat_id = qwen_service.create_new_chat(model)
                                if new_chat_id:
                                    logger.info(f"New chat created with ID: {new_chat_id}")
                                    # Gửi lại request với parent_id = None
                                    qwen_data = qwen_service.prepare_qwen_request(data, new_chat_id, model)
                                    
                                    logger.info(f"Retrying request with new chat_id: {new_chat_id} and parent_id: None")
                                    retry_response = requests.post(
                                        f"{QWEN_CHAT_COMPLETIONS_URL}?chat_id={new_chat_id}",
                                        headers=QWEN_HEADERS,
                                        json=qwen_data,
                                        stream=True,
                                        timeout=300
                                    )
                                    
                                    if retry_response.status_code == 200:
                                        logger.info("Retry successful, continuing with new chat...")
                                        # Tiếp tục xử lý response từ retry
                                        response = retry_response
                                    else:
                                        logger.error(f"Retry failed with status: {retry_response.status_code}")
                                        return {'content': f'Error: Failed to retry with new chat: {retry_response.status_code}'}
                                else:
                                    logger.error("Failed to create new chat for retry")
                                    return {'content': 'Error: Failed to create new chat for retry'}
                    except json.JSONDecodeError as e:
                        logger.error(f"Error parsing JSON response: {e}")
            except Exception as e:
                logger.error(f"Error reading response content: {e}")
            
            if response.status_code == 200:
                # Capture toàn bộ content từ stream
                full_content = ""
                thinking_content = ""
                
                for line in response.iter_lines():
                    if line:
                        line_str = line.decode('utf-8')
                        if line_str.startswith('data: '):
                            try:
                                chunk_data = json.loads(line_str[6:])
                                
                                # Xử lý response.created
                                if 'response.created' in chunk_data:
                                    response_created = chunk_data['response.created']
                                    parent_id = response_created.get('parent_id')
                                    response_id = response_created.get('response_id')
                                    if parent_id and response_id:
                                        chat_manager.update_parent_info(parent_id, response_id)
                                    continue
                                
                                if chunk_data.get('choices') and chunk_data['choices'][0].get('delta'):
                                    delta = chunk_data['choices'][0]['delta']
                                    content = delta.get('content', '')
                                    phase = delta.get('phase', None)
                                    
                                    # Log phase nếu có thay đổi
                                    request_state.log_phase_change(phase)
                                    
                                    # Xử lý think mode
                                    if phase == "think":
                                        if content:
                                            thinking_content += content
                                        # Nếu think mode kết thúc, reset để chuẩn bị cho answer phase
                                        if delta.get('status') == 'finished':
                                            request_state.think_started = False
                                    
                                    elif phase == "answer" or phase is None:
                                        # Normal content (answer phase hoặc không có phase)
                                        if content:
                                            full_content += content
                                            logger.info(f"Captured content chunk: {content}")
                                            
                            except json.JSONDecodeError:
                                continue
                        elif line_str.startswith('data: [DONE]'):
                            break
                
                logger.info(f"Total captured content: {full_content}")
                logger.info(f"Total thinking content: {thinking_content}")
                return {'content': full_content, 'thinking': thinking_content}
            else:
                logger.error(f"Qwen API error: {response.status_code} - {response.text}")
                return {'content': f'Error: {response.status_code}'}
                
        except Exception as e:
            logger.error(f"Error in call_ollama_api_direct: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {'content': f'Error: {str(e)}'}

    def stream_ollama_response_non_streaming(self, data):
        """Non-streaming Ollama response format - Direct Qwen API call"""
        model = data.get('model', 'qwen3-235b-a22b')
        request_id = str(uuid.uuid4())
        
        logger.info(f"Ollama non-streaming function called with model: {model}, request_id: {request_id}")
        
        try:
            # Gọi trực tiếp Qwen API và convert sang Ollama format
            logger.info(f"Calling call_ollama_api_direct with data: {data}")
            response = self.call_ollama_api_direct(data)
            logger.info(f"Qwen API response: {response}")
            
            if response and isinstance(response, dict):
                content = response.get('content', '')
                thinking = response.get('thinking', '')
                logger.info(f"Extracted content: {content}")
                logger.info(f"Extracted thinking: {thinking}")
                
                # Format timestamp như Ollama
                created_at = datetime.now().isoformat() + "Z"
                
                ollama_response = {
                    "model": model,
                    "created_at": created_at,
                    "message": {
                        "role": "assistant",
                        "content": content
                    },
                    "done_reason": "stop",
                    "done": True,
                    "total_duration": 2497343200,
                    "load_duration": 1837218100,
                    "prompt_eval_count": 13,
                    "prompt_eval_duration": 147000000,
                    "eval_count": 31,
                    "eval_duration": 511000000
                }
                
                # Thêm thinking field nếu có
                if thinking:
                    ollama_response["message"]["thinking"] = thinking
                
                logger.info(f"Returning ollama response: {ollama_response}")
                return ollama_response
            else:
                logger.error(f"Invalid response format: {response}")
                return {"error": "Failed to get response from Qwen API"}
        
        except Exception as e:
            logger.error(f"Error in stream_ollama_response_non_streaming: {e}")
            return {"error": str(e)}

# Global Ollama service instance
ollama_service = OllamaService()
