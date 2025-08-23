import requests
import time
import uuid
import json
import logging
from config import QWEN_HEADERS, QWEN_MODELS_URL, QWEN_NEW_CHAT_URL, QWEN_CHAT_COMPLETIONS_URL

logger = logging.getLogger(__name__)

class QwenService:
    """Service để tương tác với Qwen API"""
    
    def __init__(self):
        self.models_cache = None
    
    def get_models_from_qwen(self):
        """Lấy danh sách models từ Qwen API"""
        try:
            response = requests.get(QWEN_MODELS_URL, headers=QWEN_HEADERS)
            
            if response.status_code == 200:
                models_data = response.json()
                
                # Chuyển đổi format từ Qwen sang OpenAI
                openai_models = []
                for model in models_data.get('data', []):
                    openai_models.append({
                        "id": model.get('id', 'qwen3-235b-a22b'),
                        "object": "model",
                        "owned_by": "organization_owner"
                    })
                self.models_cache = openai_models
                logger.info(f"Converted {len(openai_models)} models from Qwen API")
                return openai_models
            else:
                logger.error(f"Qwen API error: {response.status_code} - {response.text}")
                # Fallback nếu API không hoạt động - trả về models giống LM Studio
                return []
        except Exception as e:
            logger.error(f"Error fetching models from Qwen API: {e}")
            return []
    
    def create_new_chat(self, model="qwen3-235b-a22b"):
        """Tạo chat mới từ Qwen API với model được chỉ định"""
        try:
            logger.info(f"Creating new chat with model: {model}")
            chat_data = {
                "title": "New Chat",
                "models": [model],
                "chat_mode": "guest",
                "chat_type": "t2t",
                "timestamp": int(time.time() * 1000)
            }
            
            logger.info(f"Chat data: {chat_data}")
            response = requests.post(QWEN_NEW_CHAT_URL, headers=QWEN_HEADERS, json=chat_data)
            logger.info(f"Create chat response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Create chat response: {result}")
                if result.get('success'):
                    chat_id = result['data']['id']
                    logger.info(f"Created chat with ID: {chat_id}")
                    return chat_id
                else:
                    logger.error(f"Failed to create chat: {result}")
            else:
                logger.error(f"Create chat error: {response.status_code} - {response.text}")
            return None
        except Exception as e:
            logger.error(f"Error creating new chat: {e}")
            return None
    
    def prepare_qwen_request(self, data, chat_id, model, parent_id=None):
        """Chuẩn bị request data cho Qwen API"""
        qwen_data = {
            "stream": data.get('stream', False),
            "incremental_output": data.get('stream', False),
            "chat_id": chat_id,
            "chat_mode": "normal",  # Thay đổi từ "guest" sang "normal"
            "model": model,
            "parent_id": parent_id,  # Sử dụng parent_id nếu có
            "messages": [],
            "timestamp": int(time.time())
        }
        
        # Xử lý tất cả messages để tạo context đầy đủ
        messages = data.get('messages', [])
        logger.info(f"Processing {len(messages)} messages...")
        
        if messages:
            # Tạo context từ tất cả messages
            context_parts = []
            
            for i, msg in enumerate(messages):
                role = msg.get('role', '')
                content = msg.get('content', '')
                logger.info(f"Content: {content}")
                
                logger.info(f"Processing message {i+1}/{len(messages)}: role={role}, content_length={len(content)}")
                logger.info(f"Message {i+1} content preview: {content[:200]}...")
                
                if role == 'system':
                    # System message - thêm vào đầu context
                    context_parts.append(f"System: {content}")
                elif role == 'user':
                    # User message - thêm vào context
                    context_parts.append(f"User: {content}")
                elif role == 'assistant':
                    # Assistant message - thêm vào context
                    context_parts.append(f"Assistant: {content}")
                else:
                    logger.info(f"Unknown role: {role}")
            
            # Kết hợp tất cả context
            combined_content = "\n\n".join(context_parts)
            
            qwen_msg = {
                "fid": str(uuid.uuid4()),
                "parentId": parent_id,  # Sử dụng parent_id nếu có
                "childrenIds": [],
                "role": "user",  # Luôn là user role cho Qwen
                "content": combined_content,
                "user_action": "chat",
                "files": [],
                "timestamp": int(time.time()),
                "models": [model],
                "chat_type": "t2t",
                "feature_config": {
                    "thinking_enabled": True,
                    "output_schema": "phase",
                    "thinking_budget": 1024
                },
                "extra": {
                    "meta": {
                        "subChatType": "t2t"
                    }
                },
                "sub_chat_type": "t2t",
                "parent_id": parent_id  # Sử dụng parent_id nếu có
            }
            qwen_data["messages"].append(qwen_msg)
            logger.info(f"Prepared Qwen message with {len(combined_content)} characters, parent_id={parent_id}")
        
        return qwen_data

# Global Qwen service instance
qwen_service = QwenService()
