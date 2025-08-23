import logging
from services.qwen_service import qwen_service

logger = logging.getLogger(__name__)

class ChatManager:
    """Quản lý chat_id và parent_id cho server"""
    
    def __init__(self):
        self.current_chat_id = None
        self.current_parent_id = None
        self.current_response_id = None
        self.model = "qwen3-235b-a22b"
    
    def initialize_chat(self, model="qwen3-235b-a22b"):
        """Khởi tạo chat_id khi server bắt đầu"""
        self.model = model
        logger.info(f"Initializing chat with model: {model}")
        
        chat_id = qwen_service.create_new_chat(model)
        if chat_id:
            self.current_chat_id = chat_id
            self.current_parent_id = None
            self.current_response_id = None
            logger.info(f"Chat initialized with ID: {chat_id}")
            return chat_id
        else:
            logger.error("Failed to initialize chat")
            return None
    
    def get_current_chat_id(self):
        """Lấy chat_id hiện tại"""
        return self.current_chat_id
    
    def get_current_parent_id(self):
        """Lấy parent_id hiện tại"""
        return self.current_parent_id
    
    def update_parent_info(self, parent_id, response_id):
        """Cập nhật parent_id và response_id từ response"""
        self.current_parent_id = parent_id
        self.current_response_id = response_id
        logger.info(f"Updated parent_id: {parent_id}, response_id: {response_id}")
        
        # Cập nhật terminal UI
        try:
            from utils.terminal_ui import terminal_ui
            terminal_ui.update_parent_id(parent_id)
        except Exception as e:
            logger.error(f"Error updating terminal UI: {e}")
    
    def create_new_chat(self, model=None):
        """Tạo chat mới và cập nhật chat_id hiện tại"""
        if model:
            self.model = model
        
        logger.info(f"Creating new chat with model: {self.model}")
        chat_id = qwen_service.create_new_chat(self.model)
        
        if chat_id:
            self.current_chat_id = chat_id
            self.current_parent_id = None
            self.current_response_id = None
            logger.info(f"New chat created with ID: {chat_id}")
            return chat_id
        else:
            logger.error("Failed to create new chat")
            return None
    
    def reset_chat(self):
        """Reset chat_id về None"""
        self.current_chat_id = None
        self.current_parent_id = None
        self.current_response_id = None
        logger.info("Chat ID and parent info reset to None")

# Global chat manager instance
chat_manager = ChatManager()
