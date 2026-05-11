# command_handler.py
from logger_utils import get_logger
import rag_manager as rag

logger = get_logger("CommandHandler", subdir="main")

class CommandHandler:
    def __init__(self, rag_manager):
        self.rag_manager = rag_manager

    def handle(self, user_input: str) -> bool:
        """Handle all slash commands, return True if handled"""
        if not user_input.startswith('/'):
            return False

        cmd_line = user_input.strip()
        parts = cmd_line.split()
        command = parts[0].lower()

        match command:
            case "/help":
                self._show_help()
                return True

            case "/tools":
                self._show_tools_status()
                return True

            case "/setting":
                self._handle_setting(parts)
                return True

            case "/export":
                self._handle_export(parts)
                return True

            case "/delete" | "/del":
                self._handle_delete(parts)
                return True

            case _:
                print(f"❌ Unknown command: {command}")
                print("Input /help to see available commands.")
                return True

    def _show_help(self):
        print("""Available commands:
  /help                    → Show this help
  /tools                   → Show tool status
  /setting <tool> <on/off> → Enable/disable tool
  /export [day|week|all]   → Export memories
  /delete <mem_id>         → Delete memory
        """)

    def _show_tools_status(self):
        from settings import settings
        print("\n=== Current Tool Status ===")
        for tool, enabled in settings.get_all_status().items():
            status = "Enabled" if enabled else "❌ Disabled"
            confirm = " (needs confirmation)" if settings.needs_confirmation(tool) else ""
            print(f"  • {tool:15} {status}{confirm}")

    def _handle_setting(self, parts):
        from settings import settings
        if len(parts) >= 3:
            tool_name = parts[1]
            state = parts[2].lower()
            enable = state in ['on', 'true', '1', 'enable', 'yes']
            if settings.set_tool(tool_name, enable):
                print(f"Set {tool_name} → {'Enabled' if enable else 'Disabled'}")
            else:
                print(f"Unknown tool: {tool_name}")
        else:
            print("Usage: /setting <tool_name> <on/off>")

    def _handle_export(self, parts):
        time_arg = parts[1] if len(parts) > 1 else "day"
        keyword = parts[2] if len(parts) > 2 else None
        print(f"Exporting (time: {time_arg}, keyword: {keyword})...")
        filename = self.rag_manager.export_mem_to_markdown(time_arg, keyword)
        if filename:
            print(f"Export successful! File: {filename}")
        else:
            print("Export failed or no memories found.")

    def _handle_delete(self, parts):
        if len(parts) > 1:
            mem_id = parts[1].strip()
            self.rag_manager.delete_by_id(mem_id)
            print(f"Deleted: {mem_id}")
        else:
            print("Usage: /delete <mem_id>")