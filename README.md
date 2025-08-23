# QwenToApi - Qwen API Integration

Server tùy chỉnh tích hợp với Qwen API, hỗ trợ cả LM Studio và Ollama format.

## Tính năng

- **Dual Mode**: Hỗ trợ cả LM Studio (port 1235) và Ollama (port 11434)
- **Think Mode**: Hỗ trợ tính năng suy nghĩ của Qwen với `<think>` tags
- **Image Support**: Hỗ trợ xử lý hình ảnh base64 (Ollama mode)
- **Queue System**: Hệ thống xếp hàng để xử lý request đồng thời
- **Background Mode**: Chạy server trong background không có output

## Cài đặt

```bash
pip install -r requirements.txt
```

## Sử dụng

### Chạy bình thường
```bash
python server.py
```

### Chạy với argument

```bash
# Chạy trong background mode (không có output)
python server.py --background

# Chỉ định mode
python server.py --mode lmstudio
python server.py --mode ollama

# Chỉ định port
python server.py --port 1235
python server.py --port 11434

# Chỉ định host
python server.py --host 127.0.0.1

# Kết hợp nhiều argument
python server.py --background --mode ollama --port 11434
```

### Arguments

- `--background`: Chạy server trong background mode, redirect tất cả output về null
- `--mode`: Chỉ định mode server (`lmstudio` hoặc `ollama`)
- `--port`: Chỉ định port server (mặc định: 1235 cho lmstudio, 11434 cho ollama)
- `--host`: Chỉ định host server (mặc định: 0.0.0.0)

### Background Mode

Khi chạy với `--background`:
- Tất cả output (stdout, stderr) được redirect về null
- Không có terminal UI
- Server chạy im lặng trong background
- Phù hợp để chạy như service hoặc daemon

## Endpoints

### LM Studio Mode (port 1235)

- `GET /v1/models` - Danh sách models
- `GET /v1/models/{model_id}` - Thông tin model
- `POST /v1/chat/completions` - Chat completions
- `POST /v1/completions` - Text completions (deprecated)
- `POST /v1/embeddings` - Embeddings (not supported)

### Ollama Mode (port 11434)

- `GET /api/version` - Phiên bản Ollama
- `GET /api/tags` - Danh sách models
- `GET /api/ps` - Models đang chạy
- `POST /api/show` - Thông tin model
- `POST /api/generate` - Generate response
- `POST /api/chat` - Chat endpoint

## Think Mode

### LM Studio
```json
{
  "model": "qwen3-235b-a22b",
  "messages": [{"role": "user", "content": "Hãy suy nghĩ về câu hỏi này"}],
  "stream": true
}
```

Response sẽ có `<think>` tags:
```
<think>Đang suy nghĩ về câu hỏi...</think>
Câu trả lời của tôi là...
```

### Ollama
```json
{
  "model": "qwen3-235b-a22b",
  "messages": [{"role": "user", "content": "Hãy suy nghĩ về câu hỏi này"}],
  "stream": true
}
```

Response sẽ có `thinking` field:
```json
{
  "model": "qwen3-235b-a22b",
  "message": {
    "role": "assistant",
    "thinking": "Đang suy nghĩ về câu hỏi...",
    "content": "Câu trả lời của tôi là..."
  }
}
```

## Logs

Logs được lưu trong thư mục `logs/` với format ngày tháng.

## Queue System

Server sử dụng hệ thống xếp hàng để xử lý request đồng thời:
- Timeout: 2 phút
- Request timeout: 60 giây
- Chỉ xử lý 1 request tại một thời điểm

## Troubleshooting

### Server không khởi động
- Kiểm tra port có đang được sử dụng không
- Kiểm tra API key trong config.py
- Kiểm tra kết nối internet

### Request bị timeout
- Server đang xử lý request khác
- Đợi 2 phút hoặc restart server

### Think mode không hoạt động
- Đảm bảo model hỗ trợ think mode
- Kiểm tra response format

## License

MIT License
