# LM Studio Custom Server - Qwen API Integration

Custom server cho LM Studio với tích hợp Qwen API, hỗ trợ think mode và terminal UI.

## Tính năng

- ✅ **Qwen API Integration**: Tích hợp với Qwen API
- ✅ **Think Mode Support**: Hỗ trợ `<think>` và `</think>` tags
- ✅ **Queue System**: Quản lý queue cho multiple requests
- ✅ **Terminal UI**: Giao diện terminal với user input
- ✅ **Chat Session Management**: Quản lý chat_id cho session
- ✅ **Daily Logs**: Log theo ngày trong thư mục `logs/`

## Cấu trúc thư mục

```
custom_server_lmstudio/
├── server.py              # Main server file
├── config.py              # Cấu hình API keys và URLs
├── requirements.txt       # Dependencies
├── utils/                 # Utility functions
│   ├── logging_config.py  # Cấu hình logging
│   ├── queue_manager.py   # Quản lý queue và lock
│   ├── terminal_ui.py     # Terminal UI
│   └── chat_manager.py    # Quản lý chat_id
├── services/              # Business logic services
│   ├── qwen_service.py    # Service tương tác với Qwen API
│   └── chat_service.py    # Service xử lý chat completions
└── models/                # Data models
    └── request_state.py   # RequestState class
```

## Cài đặt

1. Clone repository
2. Cài đặt dependencies:
```bash
pip install -r requirements.txt
```

3. Cấu hình API keys trong `config.py`

## Chạy server

```bash
python server.py
```

## Terminal UI

Khi chạy server, terminal sẽ hiển thị:

```
================================================================================
🚀 LM Studio Custom Server - Qwen API Integration
================================================================================
📍 Current Route: No active route
💬 Chat ID: abc123-def456-ghi789
🔗 Parent ID: def456-ghi789-jkl012
--------------------------------------------------------------------------------
📊 Server Status:
   • Status: Running
   • Port: 1235
   • Host: 0.0.0.0
   • Logs: logs/
--------------------------------------------------------------------------------
💡 Available Commands:
   • 'help' - Show this help
   • 'status' - Show server status
   • 'logs' - Show recent logs
   • 'new_chat' - Create new chat session
   • 'debug' - Show debug info
   • 'clear' - Clear terminal
   • 'quit' - Stop server
--------------------------------------------------------------------------------
🎯 Enter command or press Enter to continue:
> 
```

## Chat Session Management

- **Khởi tạo**: Server tự động tạo chat_id khi khởi động
- **Sử dụng**: Tất cả requests sử dụng cùng chat_id cho đến khi:
  - Server restart
  - Gọi lệnh `new_chat`
- **Lệnh `new_chat`**: Tạo chat session mới và cập nhật chat_id
- **Parent ID**: Tự động quản lý parent_id từ response của Qwen API
  - Lấy parent_id từ `response.created` trong response
  - Sử dụng parent_id cho request tiếp theo
  - Reset parent_id khi tạo chat mới

## Logs

- **File logs**: `logs/YYYY-MM-DD.log`
- **Terminal**: Chỉ hiển thị route info và errors
- **Console**: Hiển thị tất cả logs chi tiết

## API Endpoints

- `GET /v1/models` - List models
- `POST /v1/chat/completions` - Chat completions (streaming/non-streaming)
- `GET /v1/queue/status` - Queue status
- `POST /v1/queue/reset` - Reset queue
- `POST /v1/debug/messages` - Debug message processing

## Think Mode

Server hỗ trợ think mode của Qwen:
- Gửi `<think>` tag khi bắt đầu think mode
- Stream content trong think mode
- Gửi `</think>` tag khi kết thúc think mode
- Chuyển sang answer mode bình thường
