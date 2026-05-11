# command_handler.py
from src.logger_utils import get_logger
from .rag_manager import RAGManager as rag

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
        from .settings import settings
        print("\n=== Current Tool Status ===")
        for tool, enabled in settings.get_all_status().items():
            status = "Enabled" if enabled else "Disabled"
            confirm = "True" if settings.needs_confirmation(tool) else "False"
            print(f"  • {tool:15} {status} (Need Confirmation: {confirm})")

    def _handle_setting(self, parts):
        """handle /setting command"""
        from src.settings import settings

        if len(parts) < 3:
            print("Usage:")
            print("  /setting <tool> on/off          → Enable or disable tool")
            print("  /setting <tool> confirm on/off  → Set confirmation requirement")
            return

        tool_name = parts[1]
        action = parts[2].lower()

        # /setting <tool> confirm on/off
        if action == "confirm" and len(parts) >= 4:
            require = parts[3].lower() in ['on', 'true', '1', 'yes']
            if settings.set_confirmation(tool_name, require):
                print(f"Confirmation for '{tool_name}' set to {'ON' if require else 'OFF'}")
            else:
                print(f"Unknown tool: {tool_name}")
            return

        # /setting <tool> on/off
        enable = action in ['on', 'true', '1', 'enable', 'yes']
        if settings.set_tool(tool_name, enable):
            print(f"Tool '{tool_name}' → {'Enabled' if enable else 'Disabled'}")
        else:
            print(f"Unknown tool: {tool_name}")

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