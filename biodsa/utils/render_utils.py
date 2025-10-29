# ANSI color codes for terminal output
from langchain_core.messages import BaseMessage

class TerminalColors:
    """ANSI color codes for colored terminal output."""
    # Text colors
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    MAGENTA = '\033[95m'
    WHITE = '\033[97m'
    GRAY = '\033[90m'
    
    # Styles
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    
    # Reset
    RESET = '\033[0m'
    
    # Background colors
    BG_BLUE = '\033[44m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_RED = '\033[41m'


def render_message_colored(message: BaseMessage, show_tool_calls: bool = True) -> str:
    """
    Render a LangChain message with colored formatting for terminal output.
    
    Args:
        message: The message to render (AIMessage, HumanMessage, ToolMessage, etc.)
        show_tool_calls: Whether to display tool call details for AI messages
    
    Returns:
        Formatted colored string for terminal output
    """
    msg_type = message.type
    content = message.content if message.content else ""
    
    # Build the output
    output_lines = []
    
    # Header with message type
    if msg_type == "ai":
        header = f"{TerminalColors.BOLD}{TerminalColors.BLUE}🤖 AI Assistant{TerminalColors.RESET}"
        output_lines.append("=" * 100)
        output_lines.append(header)
        output_lines.append("=" * 100)
        
        # Show content - handle both string and list formats
        if content:
            if isinstance(content, list):
                # Content is a list of blocks (text and tool_use)
                for block in content:
                    if isinstance(block, dict):
                        if block.get('type') == 'text':
                            text_content = block.get('text', '')
                            if text_content:
                                output_lines.append(f"{TerminalColors.CYAN}{text_content}{TerminalColors.RESET}")
                        elif block.get('type') == 'tool_use' and show_tool_calls:
                            # Optionally show tool_use blocks inline
                            # (usually these are also in message.tool_calls, so we might skip)
                            pass
            else:
                # Content is a string
                output_lines.append(f"{TerminalColors.CYAN}{content}{TerminalColors.RESET}")
        
        # Show tool calls if present
        if show_tool_calls and hasattr(message, 'tool_calls') and message.tool_calls:
            output_lines.append(f"\n{TerminalColors.YELLOW}📞 Tool Calls:{TerminalColors.RESET}")
            for i, tool_call in enumerate(message.tool_calls, 1):
                tool_name = tool_call.get('name', 'unknown')
                tool_args = tool_call.get('args', {})
                output_lines.append(f"  {TerminalColors.BOLD}{i}. {tool_name}{TerminalColors.RESET}")
                for key, value in tool_args.items():
                    # Truncate long values
                    value_str = str(value)
                    if len(value_str) > 100:
                        value_str = value_str[:97] + "..."
                    output_lines.append(f"     {TerminalColors.GRAY}{key}:{TerminalColors.RESET} {value_str}")
    
    elif msg_type == "human":
        header = f"{TerminalColors.BOLD}{TerminalColors.GREEN}👤 Human{TerminalColors.RESET}"
        output_lines.append("=" * 100)
        output_lines.append(header)
        output_lines.append("=" * 100)
        output_lines.append(f"{TerminalColors.GREEN}{content}{TerminalColors.RESET}")
    
    elif msg_type == "tool":
        header = f"{TerminalColors.BOLD}{TerminalColors.MAGENTA}🔧 Tool Response{TerminalColors.RESET}"
        tool_name = getattr(message, 'name', 'unknown')
        output_lines.append("=" * 100)
        output_lines.append(f"{header} {TerminalColors.GRAY}({tool_name}){TerminalColors.RESET}")
        output_lines.append("=" * 100)
        
        # Truncate very long tool responses
        if len(content) > 1000:
            content = content[:997] + "..."
        output_lines.append(f"{TerminalColors.MAGENTA}{content}{TerminalColors.RESET}")
    
    elif msg_type == "system":
        header = f"{TerminalColors.BOLD}{TerminalColors.YELLOW}⚙️  System{TerminalColors.RESET}"
        output_lines.append("=" * 100)
        output_lines.append(header)
        output_lines.append("=" * 100)
        output_lines.append(f"{TerminalColors.YELLOW}{content}{TerminalColors.RESET}")
    
    else:
        # Unknown message type
        header = f"{TerminalColors.BOLD}{TerminalColors.WHITE}📝 {msg_type.upper()}{TerminalColors.RESET}"
        output_lines.append("=" * 100)
        output_lines.append(header)
        output_lines.append("=" * 100)
        output_lines.append(f"{TerminalColors.WHITE}{content}{TerminalColors.RESET}")
    
    output_lines.append("")  # Empty line at the end
    
    return "\n".join(output_lines)

