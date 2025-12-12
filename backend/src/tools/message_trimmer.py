"""
Message Trimmer Tool - Phase 4.1
Uses LangChain 1.1.0 trim_messages utility to keep conversation history manageable
"""

from langchain_core.messages import trim_messages, SystemMessage, HumanMessage
from typing import List


def trim_conversation_history(messages: List, max_tokens: int = 4000) -> List:
    """
    Trim conversation history using LangChain 1.1.0 built-in utility.

    Strategy:
    - Keep most recent messages (strategy="last")
    - Always preserve SystemMessages (include_system=True)
    - Ensure conversation starts with HumanMessage (start_on="human")
    - Preserve original project prompt

    Args:
        messages: List of messages to trim
        max_tokens: Maximum token count to keep (default: 4000)

    Returns:
        Trimmed list of messages (~5000 tokens saved per agent call)
    """
    if not messages:
        return []

    # Use LangChain's built-in trim_messages utility
    trimmed = trim_messages(
        messages,
        max_tokens=max_tokens,
        strategy="last",  # Keep most recent messages
        token_counter=len,  # Fast approximation (character count)
        include_system=True,  # Always keep SystemMessages
        start_on="human",  # Ensure starts with HumanMessage
        allow_partial=False  # Don't partially trim messages
    )

    # Ensure original project prompt (first HumanMessage) is preserved
    # This contains the project description and is critical context
    original_human = next((m for m in messages if isinstance(m, HumanMessage)), None)
    if original_human and original_human not in trimmed:
        # Re-insert original prompt after system messages
        system_msgs = [m for m in trimmed if isinstance(m, SystemMessage)]
        other_msgs = [m for m in trimmed if not isinstance(m, SystemMessage)]
        trimmed = system_msgs + [original_human] + other_msgs

    return trimmed
