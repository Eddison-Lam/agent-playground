Feature: CLI Slash Command Handling
    As a user
    I want to use slash commands in the CLI interface
    So that I can manage my agent's knowledge base and settings more efficiently

    Background: System is successfully initialized
        Given the conversation manager is started with mock components

    # === Handling /help Command ===

    Scenario: Execute /help command to get usage instructions
        When the user inputs "/help"
        Then the session status should be "command_handled"
        And the screen output should contain "Available commands:"

    # === Handling /tools Command ===
    Scenario: Execute /tools to show tools status
        Given the following tools are registered in the settings:
            | name           | enabled | needs_confirmation |
            | web_search     | true    | false              |
            | python_sandbox | true    | true               |
            | file_manager   | false   | true               |
            | tool_d         | false   | false              |
        When the user inputs "/tools"
        Then the session status should be "command_handled"
        And the screen output should contain "Current Tool Status"

    # === Handling /setting Command ===

    Scenario: Execute /setting with insufficient arguments
        When the user inputs the command "/setting web_search"
        Then the session status should be "command_handled"
        And the screen output should contain "Usage:"

    Scenario Outline: Successfully toggle tool status
        Given the tool "web_search" is currently active
        When the user inputs the command "/setting web_search <action>"
        Then the session status should be "command_handled"
        And the screen output should contain "web_search"
        And the screen output should contain "<target_state>"
        And the tool "web_search" should be "<target_state>" in the system settings

        Examples:

        | action  | target_state |
        | off     | Disabled     |
        | on      | Enabled      |
        | enable  | Enabled      |
        | 1       | Enabled      |
    
    Scenario Outline: Successfully toggle tool confirmation requirement
        Given the tool "python_sandbox" is currently active
        When the user inputs the command "/setting python_sandbox confirm <action>"
        Then the session status should be "command_handled"
        And the screen output should contain "python_sandbox"
        And the screen output should contain "<target_output>"
        And the tool "python_sandbox" should have confirmation requirement "<target_state>" in the system settings
        
        Examples:
        | action  | target_state | target_output |
        | off     | Disabled     | OFF           |
        | on      | Enabled      | ON            |
        | enable  | Enabled      | ON            |
        | 1       | Enabled      | ON            |

    Scenario: Try to toggle confirmation for a non-existent tool
        When the user inputs the command "/setting ghost_tool confirm on"
        Then the session status should be "command_handled"
        And the screen output should contain "Unknown tool"

    Scenario Outline: Tool configuration is rejected with invalid status values
        Given the system management tool "web_search" is available
        When an operator attempts to configure "web_search" with an invalid status "<invalid_action>"
        Then the screen output should contain "Invalid value"
        And the "web_search" tool should retain its original active state

        Examples:

        | invalid_action |
        | hello          |
        | offf           |
        | 2              |

    Scenario Outline: Tool confirmation policy is protected against invalid settings
        Given the secure tool "python_sandbox" requires explicit authorization
        When an operator attempts to set the confirmation policy using an invalid value "<invalid_action>"
        Then the screen output should contain "Invalid value"
        And the "python_sandbox" confirmation policy should remain strictly enforced
        Examples:
        | invalid_action |
        | hello          |
        | offf           |
        | 2              |

    #=== Handlding /export Command ===

    Scenario: Execute /export to export rag data to markdown
    Given the RAG manager has the following data:
        | id | content           | metadata          |
        | 1  | Sample content 1  | {"source": "A"}   |
        | 2  | Sample content 2  | {"source": "B"}   |
    When the user inputs "/export"
    Then the session status should be "command_handled"
    And the screen output should contain "Export successful"

    Scenario: Execute /export with no data to export
    Given the RAG manager has no data
    When the user inputs "/export"
    Then the session status should be "command_handled"
    And the screen output should contain "failed"

    Scenario: Execute /delete or /del to delete rag data with mem_id
        Given the RAG manager has the following data:
            | id | content           | metadata          |
            | 1  | Sample content 1  | {"source": "A"}   |
            | 2  | Sample content 2  | {"source": "B"}   |
        When the user inputs "/delete 1"
        Then the session status should be "command_handled"
        And the screen output should contain "Deleted: 1"

    Scenario: Execute /delete with invalid mem_id
        Given the RAG manager has the following data:
            | id | content           | metadata          |
            | 1  | Sample content 1  | {"source": "A"}   |
            | 2  | Sample content 2  | {"source": "B"}   |
        When the user inputs "/delete 999"
        Then the session status should be "command_handled"
        And the screen output should contain "Delete failed"