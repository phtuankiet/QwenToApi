import threading
import logging

logger = logging.getLogger(__name__)

class UIManager:
    """Unified UI manager that delegates to terminal or GUI UI safely"""
    
    def __init__(self):
        self.current_ui = None
        self.ui_type = None  # 'terminal' or 'gui'
        self.lock = threading.Lock()
    
    def set_ui(self, ui_instance, ui_type):
        """Set the active UI instance"""
        with self.lock:
            self.current_ui = ui_instance
            self.ui_type = ui_type
            logger.info(f"UI Manager: Using {ui_type} UI")
    
    def update_route(self, route_info, request_body=None):
        """Thread-safe route update that delegates to the active UI"""
        with self.lock:
            if self.current_ui and hasattr(self.current_ui, 'update_route'):
                try:
                    # Check if the UI supports request body parameter
                    import inspect
                    sig = inspect.signature(self.current_ui.update_route)
                    if len(sig.parameters) > 1:
                        # UI supports request body parameter
                        self.current_ui.update_route(route_info, request_body)
                    else:
                        # Legacy UI, only pass route info
                        self.current_ui.update_route(route_info)
                except Exception as e:
                    logger.error(f"Error updating route in {self.ui_type} UI: {e}")
    
    def update_chat_id(self, chat_id):
        """Thread-safe chat ID update that delegates to the active UI"""
        with self.lock:
            if self.current_ui and hasattr(self.current_ui, 'update_chat_id'):
                try:
                    self.current_ui.update_chat_id(chat_id)
                except Exception as e:
                    logger.error(f"Error updating chat ID in {self.ui_type} UI: {e}")
    
    def update_parent_id(self, parent_id):
        """Thread-safe parent ID update that delegates to the active UI"""
        with self.lock:
            if self.current_ui and hasattr(self.current_ui, 'update_parent_id'):
                try:
                    self.current_ui.update_parent_id(parent_id)
                except Exception as e:
                    logger.error(f"Error updating parent ID in {self.ui_type} UI: {e}")
    
    def update_server_info(self, mode, port):
        """Thread-safe server info update that delegates to the active UI"""
        with self.lock:
            if self.current_ui and hasattr(self.current_ui, 'update_server_info'):
                try:
                    self.current_ui.update_server_info(mode, port)
                except Exception as e:
                    logger.error(f"Error updating server info in {self.ui_type} UI: {e}")

    def add_chat_messages(self, user_text: str, assistant_text: str):
        """Append chat history: only user request and full Qwen response"""
        with self.lock:
            try:
                if not self.current_ui:
                    return
                # Prefer dedicated method if exists, else fallback to _add_to_chat_history
                if hasattr(self.current_ui, '_add_to_chat_history'):
                    self.current_ui._add_to_chat_history(f"User: {user_text}")
                    self.current_ui._add_to_chat_history(f"Assistant: {assistant_text}")
                elif hasattr(self.current_ui, 'log'):
                    # Fallback to logs tab
                    self.current_ui.log(f"CHAT User: {user_text}")
                    self.current_ui.log(f"CHAT Assistant: {assistant_text}")
            except Exception as e:
                logger.error(f"Error adding chat messages to {self.ui_type} UI: {e}")

    def update_queue_status(self, processing: bool, queue_size: int):
        """Update queue processing flag and size in the active UI"""
        with self.lock:
            try:
                if not self.current_ui:
                    return
                if hasattr(self.current_ui, 'update_queue_status'):
                    self.current_ui.update_queue_status(processing, queue_size)
            except Exception as e:
                logger.error(f"Error updating queue status in {self.ui_type} UI: {e}")

# Global UI manager instance
ui_manager = UIManager()
