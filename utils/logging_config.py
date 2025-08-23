import logging
import os
from datetime import datetime

def setup_logging():
    """Cấu hình logging cho server"""
    # Tạo thư mục logs nếu chưa có
    log_dir = os.path.expanduser("logs")
    os.makedirs(log_dir, exist_ok=True)
    
    # File handler cho tất cả logs với tên file theo ngày
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = os.path.join(log_dir, f"{today}.log")
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter('%(asctime)s  [%(levelname)s]\n [LM STUDIO SERVER] %(message)s')
    file_handler.setFormatter(file_formatter)
    
    # Console handler chỉ cho route info và errors
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(asctime)s  [%(levelname)s] %(message)s')
    console_handler.setFormatter(console_formatter)
    
    # Tạo custom filter để chỉ log route info ra console
    class RouteFilter(logging.Filter):
        def filter(self, record):
            return 'ROUTE:' in record.getMessage() or record.levelno >= logging.WARNING
    
    console_handler.addFilter(RouteFilter())
    
    # Cấu hình root logger
    logging.basicConfig(
        level=logging.INFO,
        handlers=[file_handler, console_handler]
    )
    
    return logging.getLogger(__name__)
