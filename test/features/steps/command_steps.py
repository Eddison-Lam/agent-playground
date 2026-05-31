"""Steps for slash command handling."""
from behave import given, when, then
from unittest.mock import Mock, MagicMock, patch
import sys
from io import StringIO

# ====================== General Steps ======================

@when('the user inputs "{command}"')
def step_user_inputs_command(context, command):
    context.output_buffer = StringIO()
    
    try:
        with patch('sys.stdout', context.output_buffer):
            result = context.command_handler.handle(command)
            context.command_result = result
            context.session_status = "command_handled"
    except Exception as e:
        context.session_status = "command_error"
        context.error = str(e)


@then('the screen output should contain "{text}"')
def step_check_output_contains(context, text):
    output = context.output_buffer.getvalue()
    assert text in output, \
        f"Expected '{text}' in output.\nActual output:\n{output}"


# ====================== Background & Setup ======================

@given("the conversation manager is started with mock components")
def step_start_conversation_manager(context):
    """Initialize conversation manager with mocks."""
    from src.command_handler import CommandHandler
    from src.rag_manager import RAGManager
    
    context.mock_rag_manager = MagicMock(spec=RAGManager)
    context.command_handler = CommandHandler(context.mock_rag_manager)
    context.output_buffer = StringIO()
    context.session_status = None


# ====================== /help Command ======================

@then('the session status should be "{status}"')
def step_check_session_status(context, status):
    assert context.session_status == status


# ====================== /tools Command ======================

@given("the following tools are registered in the settings:")
def step_register_tools(context):
    """Register tools with specific configurations."""
    from src.settings import settings
    
    for row in context.table:
        tool_name = row["name"]
        enabled = row["enabled"].lower() == "true"
        needs_confirmation = row["needs_confirmation"].lower() == "true"
        
        settings.set_tool(tool_name, enabled)
        settings.set_confirmation(tool_name, needs_confirmation)
    
    context.tools = {row["name"]: row for row in context.table}


# ====================== /setting Command ======================

@given('the tool "{tool_name}" is currently active')
def step_tool_is_active(context, tool_name):
    """Ensure tool is enabled."""
    from src.settings import settings
    settings.set_tool(tool_name, True)
    context.tool_name = tool_name


@when('the user inputs the command "{command}"')
def step_user_inputs_setting_command(context, command):
    """User inputs a /setting command."""
    context.output_buffer = StringIO()
    
    try:
        with patch('sys.stdout', context.output_buffer):
            result = context.command_handler.handle(command)
            context.command_result = result
            context.session_status = "command_handled"
    except Exception as e:
        context.session_status = "command_error"
        context.error = str(e)


@then('the tool "{tool_name}" should be "{state}" in the system settings')
def step_check_tool_state(context, tool_name, state):
    """Check tool's enabled/disabled state."""
    from src.settings import settings
    
    is_enabled = settings.is_enabled(tool_name)
    expected_enabled = state.lower() == "enabled"
    
    assert is_enabled == expected_enabled, \
        f"Tool '{tool_name}' expected to be {state}, but is {'enabled' if is_enabled else 'disabled'}"


@then('the tool "{tool_name}" should have confirmation requirement "{state}" in the system settings')
def step_check_confirmation_requirement(context, tool_name, state):
    """Check tool's confirmation requirement."""
    from src.settings import settings
    
    needs_confirmation = settings.needs_confirmation(tool_name)
    expected_needs_confirmation = state.lower() == "enabled"
    
    assert needs_confirmation == expected_needs_confirmation, \
        f"Tool '{tool_name}' confirmation expected to be {state}, but is {'enabled' if needs_confirmation else 'disabled'}"


@given('the system management tool "{tool_name}" is available')
def step_tool_is_available(context, tool_name):
    """Ensure tool exists in system."""
    from src.settings import settings
    context.original_tool_state = settings.is_enabled(tool_name)
    context.tool_name = tool_name


@when('an operator attempts to configure "{tool_name}" with an invalid status "{invalid_action}"')
def step_configure_with_invalid_status(context, tool_name, invalid_action):
    """Try to configure tool with invalid status."""
    context.output_buffer = StringIO()
    
    command = f"/setting {tool_name} {invalid_action}"
    try:
        with patch('sys.stdout', context.output_buffer):
            result = context.command_handler.handle(command)
            context.command_result = result
            context.session_status = "command_handled"
    except Exception as e:
        context.session_status = "command_error"
        context.error = str(e)


@then('the "{tool_name}" tool should retain its original active state')
def step_tool_retains_original_state(context, tool_name):
    """Verify tool state hasn't changed."""
    from src.settings import settings
    
    current_state = settings.is_enabled(tool_name)
    assert current_state == context.original_tool_state, \
        f"Tool state changed unexpectedly"


@given('the secure tool "{tool_name}" requires explicit authorization')
def step_tool_requires_confirmation(context, tool_name):
    """Ensure tool has confirmation enabled."""
    from src.settings import settings
    settings.set_confirmation(tool_name, True)
    context.original_confirmation = settings.needs_confirmation(tool_name)
    context.tool_name = tool_name


@when('an operator attempts to set the confirmation policy using an invalid value "{invalid_action}"')
def step_set_confirmation_with_invalid_value(context, invalid_action):
    """Try to set confirmation with invalid value."""
    context.output_buffer = StringIO()
    
    command = f"/setting {context.tool_name} confirm {invalid_action}"
    try:
        with patch('sys.stdout', context.output_buffer):
            result = context.command_handler.handle(command)
            context.command_result = result
            context.session_status = "command_handled"
    except Exception as e:
        context.session_status = "command_error"
        context.error = str(e)


@then('the "{tool_name}" confirmation policy should remain strictly enforced')
def step_confirmation_remains_enforced(context, tool_name):
    """Verify confirmation requirement hasn't changed."""
    from src.settings import settings
    
    current_confirmation = settings.needs_confirmation(tool_name)
    assert current_confirmation == context.original_confirmation, \
        f"Confirmation policy changed unexpectedly"


# ====================== /export Command ======================

@given("the RAG manager has the following data:")
def step_rag_manager_has_data(context):
    """Set up RAG manager with sample data."""
    context.mock_rag_manager.export_mem_to_markdown = Mock(return_value="export.md")
    context.rag_data = []
    
    def mock_delete(mem_id: str) -> bool:
        valid_ids = [row["id"] for row in context.table]
        return mem_id in valid_ids
    
    context.mock_rag_manager.delete_by_id = Mock(side_effect=mock_delete)
    
    for row in context.table:
        context.rag_data.append({
            "id": row["id"],
            "content": row["content"],
            "metadata": row["metadata"]
        })

    valid_ids = [row["id"] for row in context.table]
    
    context.mock_rag_manager.delete_by_id = Mock(
        side_effect=lambda mem_id: mem_id in valid_ids
    )


@given("the RAG manager has no data")
def step_rag_manager_has_no_data(context):
    """Set up empty RAG manager."""
    context.mock_rag_manager.export_mem_to_markdown = Mock(return_value=None)
    context.rag_data = []

# ====================== Cleanup ======================

def after_scenario(context, scenario):
    """Clean up after each scenario."""
    if hasattr(context, 'output_buffer'):
        context.output_buffer.close()
    print(f"[DEBUG] Scenario '{scenario.name}' cleanup done")