import time
import logging

logger = logging.getLogger(__name__)

class RequestState:
    """Quản lý state cho mỗi request riêng biệt"""
    def __init__(self, request_id, model):
        self.request_id = request_id
        self.model = model
        self.think_started = False
        self.current_phase = None
        self.chunk_count = 0
        self.start_time = time.time()
    
    def log_phase_change(self, phase):
        """Log khi phase thay đổi"""
        if phase and self.current_phase != phase:
            if self.current_phase is None:
                logger.info(f"Request {self.request_id} phase: {phase}")
            else:
                logger.info(f"Request {self.request_id} phase changed from {self.current_phase} to {phase}")
            self.current_phase = phase
