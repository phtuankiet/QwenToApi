import time
import threading
from collections import deque
import logging

logger = logging.getLogger(__name__)

class QueueManager:
    """Quản lý queue và lock cho chat completions"""
    
    def __init__(self):
        self.chat_queue = deque()
        self.chat_lock = threading.Lock()
        self.current_processing = False
        self.current_processing_start_time = None
    
    def reset_lock_if_stuck(self):
        """Reset lock nếu nó bị treo quá 2 phút"""
        if self.current_processing and self.current_processing_start_time:
            stuck_duration = time.time() - self.current_processing_start_time
            if stuck_duration > 120:  # 2 phút
                logger.warning(f"Lock stuck for {stuck_duration:.1f} seconds, resetting...")
                with self.chat_lock:
                    self.current_processing = False
                    self.current_processing_start_time = None
                return True
            elif stuck_duration > 30:  # Log sau 30 giây
                logger.info(f"Lock has been active for {stuck_duration:.1f} seconds")
        return False
    
    def acquire_lock(self, request_id):
        """Acquire lock cho request"""
        start_wait_time = time.time()
        wait_timeout = 60  # 60 giây timeout
        
        while True:
            # Kiểm tra timeout
            if time.time() - start_wait_time > wait_timeout:
                logger.error(f"Request {request_id} timed out waiting for lock after {wait_timeout} seconds")
                return False
            
            # Kiểm tra và reset lock nếu bị treo
            self.reset_lock_if_stuck()
            
            with self.chat_lock:
                if not self.current_processing:
                    self.current_processing = True
                    self.current_processing_start_time = time.time()
                    logger.info(f"Request {request_id} starting processing")
                    return True
                else:
                    # Log thời gian chờ và trạng thái lock
                    wait_duration = time.time() - start_wait_time
                    lock_duration = time.time() - self.current_processing_start_time if self.current_processing_start_time else 0
                    if wait_duration > 5:  # Log sau 5 giây chờ
                        logger.info(f"Request {request_id} waiting for lock... (waited {wait_duration:.1f}s, lock active {lock_duration:.1f}s)")
            
            # Đợi một chút trước khi kiểm tra lại
            time.sleep(0.1)
    
    def release_lock(self, request_id):
        """Release lock sau khi hoàn thành"""
        with self.chat_lock:
            self.current_processing = False
            self.current_processing_start_time = None
            logger.info(f"Request {request_id} completed/failed, releasing lock")
    
    def get_status(self):
        """Lấy trạng thái queue"""
        with self.chat_lock:
            status = {
                "current_processing": self.current_processing,
                "queue_size": len(self.chat_queue),
                "queue_items": [],
                "lock_info": {}
            }
            
            if self.current_processing and self.current_processing_start_time:
                processing_duration = time.time() - self.current_processing_start_time
                status["processing_duration"] = processing_duration
                status["processing_start_time"] = self.current_processing_start_time
                status["lock_info"] = {
                    "active": True,
                    "duration_seconds": processing_duration,
                    "start_time": self.current_processing_start_time
                }
            else:
                status["lock_info"] = {
                    "active": False,
                    "duration_seconds": 0,
                    "start_time": None
                }
            
            # Lấy thông tin các request trong queue (không expose data nhạy cảm)
            for i, (request_id, data) in enumerate(self.chat_queue):
                status["queue_items"].append({
                    "position": i + 1,
                    "request_id": request_id,
                    "model": data.get('model', 'unknown'),
                    "stream": data.get('stream', False)
                })
            
            return status
    
    def reset_queue(self):
        """Reset queue và lock (emergency function)"""
        with self.chat_lock:
            was_processing = self.current_processing
            processing_duration = time.time() - self.current_processing_start_time if self.current_processing_start_time else 0
            
            self.current_processing = False
            self.current_processing_start_time = None
            self.chat_queue.clear()
            
            if was_processing:
                logger.warning(f"Queue and lock manually reset (was processing for {processing_duration:.1f}s)")
            else:
                logger.warning("Queue and lock manually reset")
            
            return {
                "message": "Queue and lock reset successfully",
                "status": "reset",
                "was_processing": was_processing,
                "processing_duration": processing_duration
            }

# Global queue manager instance
queue_manager = QueueManager()
