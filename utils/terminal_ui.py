import threading
import time
import os
import sys
from datetime import datetime

class TerminalUI:
    """Terminal UI cho user input và hiển thị route info"""
    
    def __init__(self):
        self.current_route = "No active route"
        self.current_chat_id = None
        self.current_parent_id = None
        self.input_thread = None
        self.running = False
        self.lock = threading.Lock()
    
    def start(self):
        """Bắt đầu terminal UI"""
        self.running = True
        self.input_thread = threading.Thread(target=self._input_loop, daemon=True)
        self.input_thread.start()
        self._print_ui()
    
    def stop(self):
        """Dừng terminal UI"""
        self.running = False
        if self.input_thread:
            self.input_thread.join(timeout=1)
    
    def update_route(self, route_info):
        """Cập nhật thông tin route hiện tại"""
        with self.lock:
            self.current_route = route_info
            self._print_ui()
    
    def update_chat_id(self, chat_id):
        """Cập nhật chat_id hiện tại"""
        with self.lock:
            self.current_chat_id = chat_id
            self._print_ui()
    
    def update_parent_id(self, parent_id):
        """Cập nhật parent_id hiện tại"""
        with self.lock:
            self.current_parent_id = parent_id
            self._print_ui()
    
    def _print_ui(self):
        """In UI ra terminal"""
        os.system('cls' if os.name == 'nt' else 'clear')
        
        # Header
        print("=" * 80)
        print("🚀 LM Studio Custom Server - Qwen API Integration")
        print("=" * 80)
        
        # Current route info
        print(f"📍 Current Route: {self.current_route}")
        
        # Current chat ID
        chat_status = f"💬 Chat ID: {self.current_chat_id}" if self.current_chat_id else "💬 Chat ID: Not initialized"
        print(chat_status)
        
        # Current parent ID
        parent_status = f"🔗 Parent ID: {self.current_parent_id}" if self.current_parent_id else "🔗 Parent ID: None"
        print(parent_status)
        print("-" * 80)
        
        # Server status
        print("📊 Server Status:")
        print("   • Status: Running")
        print("   • Port: 1235")
        print("   • Host: 0.0.0.0")
        print("   • Logs: logs/")
        print("-" * 80)
        
        # Available commands
        print("💡 Available Commands:")
        print("   • 'help' - Show this help")
        print("   • 'status' - Show server status")
        print("   • 'logs' - Show recent logs")
        print("   • 'new_chat' - Create new chat session")
        print("   • 'debug' - Show debug info")
        print("   • 'clear' - Clear terminal")
        print("   • 'quit' - Stop server")
        print("-" * 80)
        
        # Input area
        print("🎯 Enter command or press Enter to continue:")
        print("> ", end="", flush=True)
    
    def _input_loop(self):
        """Loop xử lý input từ user"""
        while self.running:
            try:
                user_input = input().strip()
                if user_input:
                    self._handle_command(user_input)
                else:
                    # Refresh UI khi user chỉ nhấn Enter
                    self._print_ui()
            except (EOFError, KeyboardInterrupt):
                break
            except Exception as e:
                print(f"Error handling input: {e}")
    
    def _handle_command(self, command):
        """Xử lý command từ user"""
        command = command.lower()
        
        if command == 'help':
            self._print_ui()
        elif command == 'status':
            self._show_status()
        elif command == 'logs':
            self._show_logs()
        elif command == 'new_chat':
            self._create_new_chat()
        elif command == 'debug':
            self._show_debug_info()
        elif command == 'clear':
            self._print_ui()
        elif command == 'quit':
            print("🛑 Stopping server...")
            os._exit(0)
        else:
            print(f"❌ Unknown command: {command}")
            print("💡 Type 'help' for available commands")
            time.sleep(2)
            self._print_ui()
    
    def _create_new_chat(self):
        """Tạo chat mới"""
        print("\n🆕 Creating new chat session...")
        try:
            # Import ở đây để tránh circular import
            from utils.chat_manager import chat_manager
            chat_id = chat_manager.create_new_chat()
            if chat_id:
                self.update_chat_id(chat_id)
                self.update_parent_id(None)  # Reset parent_id khi tạo chat mới
                print(f"✅ New chat created: {chat_id}")
            else:
                print("❌ Failed to create new chat")
        except Exception as e:
            print(f"❌ Error creating new chat: {e}")
        
        print("\nPress Enter to continue...")
        input()
        self._print_ui()
    
    def _show_status(self):
        """Hiển thị server status"""
        print("\n📊 Server Status:")
        print(f"   • Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   • Current Route: {self.current_route}")
        print(f"   • Current Chat ID: {self.current_chat_id or 'Not initialized'}")
        print(f"   • Current Parent ID: {self.current_parent_id or 'None'}")
        print(f"   • Log File: logs/{datetime.now().strftime('%Y-%m-%d')}.log")
        print("\nPress Enter to continue...")
        input()
        self._print_ui()
    
    def _show_logs(self):
        """Hiển thị recent logs"""
        try:
            log_dir = "logs"
            today = datetime.now().strftime("%Y-%m-%d")
            log_file = os.path.join(log_dir, f"{today}.log")
            
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    recent_lines = lines[-20:]  # 20 dòng cuối
                
                print(f"\n📋 Recent Logs ({log_file}):")
                print("-" * 80)
                for line in recent_lines:
                    print(line.rstrip())
            else:
                print(f"\n❌ Log file not found: {log_file}")
        except Exception as e:
            print(f"\n❌ Error reading logs: {e}")
        
        print("\nPress Enter to continue...")
        input()
        self._print_ui()
    
    def _show_debug_info(self):
        """Hiển thị debug info"""
        print("\n🔍 Debug Information:")
        print(f"   • Current Chat ID: {self.current_chat_id or 'Not initialized'}")
        print(f"   • Current Parent ID: {self.current_parent_id or 'None'}")
        print(f"   • Current Route: {self.current_route}")
        print(f"   • Server Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Thêm thông tin về chat manager
        try:
            from utils.chat_manager import chat_manager
            print(f"   • Chat Manager Chat ID: {chat_manager.get_current_chat_id() or 'None'}")
            print(f"   • Chat Manager Parent ID: {chat_manager.get_current_parent_id() or 'None'}")
        except Exception as e:
            print(f"   • Chat Manager Error: {e}")
        

        print("\nPress Enter to continue...")
        input()
        self._print_ui()

# Global terminal UI instance
terminal_ui = TerminalUI()
