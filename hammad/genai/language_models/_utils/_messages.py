"""hammad.ai.llms.utils._messages"""

from typing import List

from ....cache import cached

try:
    from openai.types.chat import ChatCompletionMessageParam
except ImportError:
    raise ImportError(
        "Using the `hammad.ai.llms` extension requires the `openai` package to be installed.\n"
        "Please either install the `openai` package, or install the `hammad.ai` extension with:\n"
        "`pip install 'hammad-python[ai]'`"
    )

__all__ = [
    "format_tool_calls",
    "consolidate_system_messages",
]


@cached
def format_tool_calls(messages: List[ChatCompletionMessageParam]) -> List[ChatCompletionMessageParam]:
    """Format tool calls in messages for better conversation context.
    
    Args:
        messages: List of chat completion messages
        
    Returns:
        Messages with formatted tool calls
    """
    formatted_messages = []
    
    for message in messages:
        if message.get("role") == "assistant" and message.get("tool_calls"):
            # Create a copy of the message
            formatted_message = dict(message)
            
            # Format tool calls into readable content
            content_parts = []
            if message.get("content"):
                content_parts.append(message["content"])
            
            for tool_call in message["tool_calls"]:
                formatted_call = (
                    f"I called the function `{tool_call['function']['name']}` "
                    f"with the following arguments:\n{tool_call['function']['arguments']}"
                )
                content_parts.append(formatted_call)
            
            formatted_message["content"] = "\n\n".join(content_parts)
            # Remove tool_calls from the formatted message
            formatted_message.pop("tool_calls", None)
            
            formatted_messages.append(formatted_message)
        else:
            formatted_messages.append(message)
    
    return formatted_messages


@cached
def consolidate_system_messages(messages: List[ChatCompletionMessageParam]) -> List[ChatCompletionMessageParam]:
    """Consolidate multiple system messages into a single system message.
    
    Args:
        messages: List of chat completion messages
        
    Returns:
        Messages with consolidated system messages
    """
    system_parts = []
    other_messages = []
    
    for message in messages:
        if message.get("role") == "system":
            if message.get("content"):
                system_parts.append(message["content"])
        else:
            other_messages.append(message)
    
    # Create consolidated messages
    consolidated_messages = []
    
    if system_parts:
        consolidated_messages.append({
            "role": "system",
            "content": "\n\n".join(system_parts)
        })
    
    consolidated_messages.extend(other_messages)
    
    return consolidated_messages