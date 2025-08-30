import json
import time
import uuid
import requests
import logging
from datetime import datetime
from models.request_state import RequestState
from services.qwen_service import qwen_service
from utils.chat_manager import chat_manager
from utils.ui_manager import ui_manager
from config import QWEN_HEADERS, QWEN_CHAT_COMPLETIONS_URL
from utils.cookie_parser import build_header

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
                
        try:
            stream_start_ns = time.perf_counter_ns()
            first_token_ns = None
            output_token_count = 0
            try:
                input_token_count = 0
                for msg in data.get('messages', []):
                    txt = msg.get('content', '')
                    if isinstance(txt, str):
                        input_token_count += max(1, len(txt.strip().split()))
            except Exception:
                pass
            
            from flask import current_app
            chat_id = current_app.config.get('CURRENT_CHAT_ID')
            if not chat_id:
                logger.error("No chat ID found in app config")
                yield json.dumps({"error": "No chat ID available"}) + "\n"
                return
            
            qwen_data = qwen_service.prepare_qwen_request(data, chat_id, model)
            
            # Gọi Qwen API với streaming
            headers = build_header(QWEN_HEADERS)

            response = requests.post(
                f"{QWEN_CHAT_COMPLETIONS_URL}?chat_id={chat_id}",
                headers=headers,
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
                            # If model not found, return Ollama-style error immediately
                            if error_code == "Not_Found" and "Model not found" in str(error_details):
                                err = {"error": f"model '{data.get('model', model)}' not found"}
                                yield json.dumps(err) + "\n"
                                return
                            
                            if error_code == "Bad_Request" and "parent_id" in error_details and "not exist" in error_details:
                                logger.warning(f"Parent ID not exist error detected: {error_details}")
                                
                                from flask import current_app
                                current_chat_id = current_app.config.get('CURRENT_CHAT_ID')
                                if current_chat_id:
                                    qwen_data = qwen_service.prepare_qwen_request(data, current_chat_id, model)
                                    
                                    retry_response = requests.post(
                                        f"{QWEN_CHAT_COMPLETIONS_URL}?chat_id={current_chat_id}",
                                        headers=headers,
                                        json=qwen_data,
                                        stream=True,
                                        timeout=300
                                    )
                                    
                                    if retry_response.status_code == 200:
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
                                            "error": f"Failed to retry with current chat: {retry_response.status_code}"
                                        }
                                        yield json.dumps(error_chunk) + "\n"
                                        return
                                else:
                                    logger.error("No current chat ID available for retry")
                                    error_created_at = datetime.now().isoformat() + "Z"
                                    error_chunk = {
                                        "model": model,
                                        "created_at": error_created_at,
                                        "message": {
                                            "role": "assistant",
                                            "content": ""
                                        },
                                        "done": True,
                                        "error": "No current chat ID available for retry"
                                    }
                                    yield json.dumps(error_chunk) + "\n"
                                    return
                    except json.JSONDecodeError as e:
                        logger.error(f"Error parsing JSON response: {e}")
            except Exception as e:
                logger.error(f"Error reading response content: {e}")
            
            if response.status_code == 200:
                done_sent = False
                # Thu thập nội dung assistant để hiển thị vào Chat khi DONE
                collected_answer = []
                last_user_text = ""
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
                                        # Nếu bắt đầu think mode và chưa gửi <think> tag
                                        if not request_state.think_started:
                                            request_state.think_started = True
                                            # Gửi <think> tag
                                            ollama_chunk = {
                                                "model": model,
                                                "created_at": created_at,
                                                "message": {
                                                    "role": "assistant",
                                                    "content": "<think>"
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
                                                    "content": content
                                                },
                                                "done": False
                                            }
                                            # Ước lượng token đầu ra (số từ)
                                            output_token_count += max(1, len(content.strip().split()))
                                            yield json.dumps(ollama_chunk) + "\n"

                                        # Nếu think mode kết thúc (status finished)
                                        if delta.get('status') == 'finished':
                                            # Gửi </think> tag
                                            ollama_chunk = {
                                                "model": model,
                                                "created_at": created_at,
                                                "message": {
                                                    "role": "assistant",
                                                    "content": "</think>"
                                                },
                                                "done": False
                                            }
                                            yield json.dumps(ollama_chunk) + "\n"
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
                                            # Thu thập content
                                            try:
                                                collected_answer.append(content)
                                            except Exception:
                                                pass
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
                                        # Đẩy lịch sử chat vào UI
                                        try:
                                            full_answer = ''.join(collected_answer)
                                            # Trích user text cuối cùng từ data
                                            try:
                                                msgs = data.get('messages') or []
                                                for m in reversed(msgs):
                                                    if isinstance(m, dict) and m.get('role') == 'user':
                                                        last_user_text = str(m.get('content') or '')
                                                        break
                                            except Exception:
                                                last_user_text = last_user_text or ""
                                            ui_manager.add_chat_messages(last_user_text, full_answer)
                                        except Exception:
                                            pass
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
                            try:
                                full_answer = ''.join(collected_answer)
                                # Trích user text cuối cùng từ data
                                try:
                                    msgs = data.get('messages') or []
                                    for m in reversed(msgs):
                                        if isinstance(m, dict) and m.get('role') == 'user':
                                            last_user_text = str(m.get('content') or '')
                                            break
                                except Exception:
                                    last_user_text = last_user_text or ""
                                ui_manager.add_chat_messages(last_user_text, full_answer)
                            except Exception:
                                pass
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
            request_id = str(uuid.uuid4())
            request_state = RequestState(request_id, model)
                        
            from flask import current_app
            chat_id = current_app.config.get('CURRENT_CHAT_ID')
            if not chat_id:
                logger.error("No chat ID found in app config")
                return {'content': 'Error: No chat ID available'}
            
            qwen_data = qwen_service.prepare_qwen_request(data, chat_id, model)
            
            # Force streaming để capture content
            qwen_data['stream'] = True
            qwen_data['incremental_output'] = True
                        
            # Gọi Qwen API với streaming để capture toàn bộ content
            headers = build_header(QWEN_HEADERS)
            response = requests.post(
                f"{QWEN_CHAT_COMPLETIONS_URL}?chat_id={chat_id}",
                headers=headers,
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
                            # Map model-not-found error to Ollama-style error
                            if error_code == "Not_Found" and "Model not found" in str(error_details):
                                return {"error": f"model '{data.get('model', model)}' not found"}
                            
                            if error_code == "Bad_Request" and "parent_id" in error_details and "not exist" in error_details:
                                logger.warning(f"Parent ID not exist error detected: {error_details}")
                                
                                from flask import current_app
                                current_chat_id = current_app.config.get('CURRENT_CHAT_ID')
                                if current_chat_id:
                                    qwen_data = qwen_service.prepare_qwen_request(data, current_chat_id, model)
                                    
                                    retry_response = requests.post(
                                        f"{QWEN_CHAT_COMPLETIONS_URL}?chat_id={current_chat_id}",
                                        headers=headers,
                                        json=qwen_data,
                                        stream=True,
                                        timeout=300
                                    )
                                    
                                    if retry_response.status_code == 200:
                                        response = retry_response
                                    else:
                                        logger.error(f"Retry failed with status: {retry_response.status_code}")
                                        return {'content': f'Error: Failed to retry with current chat: {retry_response.status_code}'}
                                else:
                                    logger.error("No current chat ID available for retry")
                                    return {'content': 'Error: No current chat ID available for retry'}
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
                                            
                            except json.JSONDecodeError:
                                continue
                        elif line_str.startswith('data: [DONE]'):
                            break
                
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
                
        try:
            # Gọi trực tiếp Qwen API và convert sang Ollama format
            response = self.call_ollama_api_direct(data)
            
            if response and isinstance(response, dict):
                content = response.get('content', '')
                thinking = response.get('thinking', '')
                
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
                
                # Thêm thinking content vào content field với <think> tags nếu có
                if thinking:
                    ollama_response["message"]["content"] = f"<think>{thinking}</think>\n\n{content}"
                
                # Push to chat history (only user request and full response content)
                try:
                    user_text = ""
                    msgs = data.get('messages') or []
                    for m in reversed(msgs):
                        if isinstance(m, dict) and m.get('role') == 'user':
                            user_text = str(m.get('content') or '')
                            break
                    assistant_text = ollama_response.get('message', {}).get('content', '')
                    ui_manager.add_chat_messages(user_text, assistant_text)
                except Exception:
                    pass
                return ollama_response
            else:
                logger.error(f"Invalid response format: {response}")
                return {"error": "Failed to get response from Qwen API"}
        
        except Exception as e:
            logger.error(f"Error in stream_ollama_response_non_streaming: {e}")
            return {"error": str(e)}

# Global Ollama service instance
ollama_service = OllamaService()
