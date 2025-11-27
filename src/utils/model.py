"""
Model utility for LangChain 1.0 model-agnostic initialization

Uses init_chat_model() pattern from LangChain 1.1.0 (Nov 24, 2025)
for seamless switching between LLM providers.

Supported providers:
- Google GenAI (Gemini 2.0 Flash) - Default
- Anthropic (Claude Sonnet 4.5)
- OpenAI (GPT-4o)
"""

from langchain_core.language_models.chat_models import BaseChatModel
from langchain.chat_models import init_chat_model
import os
from typing import Optional


def get_model(
    model_override: Optional[str] = None,
    temperature: float = 0
) -> BaseChatModel:
    """
    Get LLM model using LangChain 1.0 model-agnostic pattern

    This uses init_chat_model() which automatically infers the provider
    from the model string and instantiates the correct chat model.

    Args:
        model_override: Optional model string (e.g., "anthropic:claude-sonnet-4-5-20250929")
        temperature: Model temperature (0 for deterministic, 1 for creative)

    Returns:
        Chat model instance (BaseChatModel)

    Examples:
        >>> model = get_model()  # Uses DEFAULT_MODEL env var
        >>> model = get_model("google_genai:gemini-2.0-flash-exp")
        >>> model = get_model("anthropic:claude-sonnet-4-5-20250929", temperature=0.7)

    Provider Format:
        - Google: "google_genai:gemini-2.0-flash-exp"
        - Anthropic: "anthropic:claude-sonnet-4-5-20250929"
        - OpenAI: "openai:gpt-4o"

    Note:
        The provider prefix can be omitted for well-known models:
        - "gemini-2.5-pro" → inferred as "google_genai:gemini-2.5-pro"
        - "gpt-4o" → inferred as "openai:gpt-4o"
    """
    model_name = model_override or os.getenv(
        "DEFAULT_MODEL",
        "google_genai:gemini-1.5-flash"
    )

    try:
        # LangChain 1.0 pattern: init_chat_model() automatically infers provider
        return init_chat_model(model_name, temperature=temperature)
    except Exception as e:
        print(f"⚠️  Failed to initialize {model_name}: {e}")
        print("   Falling back to Gemini 1.5 Flash...")
        # Fallback to stable Gemini with better quota
        fallback_model = os.getenv("DEFAULT_MODEL", "google_genai:gemini-1.5-flash")
        return init_chat_model(fallback_model, temperature=temperature)


def get_cheap_model() -> BaseChatModel:
    """
    Get cheapest model for simple tasks (e.g., summarization, routing)

    Returns:
        Model from DEFAULT_MODEL env var (defaults to Gemini 1.5 Flash)

    Example:
        >>> model = get_cheap_model()
        >>> result = model.invoke([{"role": "user", "content": "Hello"}])
    """
    # Use DEFAULT_MODEL from .env instead of hardcoded value
    return get_model(temperature=0)


def get_smart_model() -> BaseChatModel:
    """
    Get best model for complex tasks (e.g., coding, reasoning)

    Tries Claude Sonnet 4.5 first (if API key available),
    falls back to Gemini 2.0 Flash.

    Returns:
        Claude Sonnet 4.5 or Gemini 2.0 Flash

    Example:
        >>> model = get_smart_model()
        >>> result = model.invoke([{"role": "user", "content": "Write a binary search"}])
    """
    # Try Claude first (best for coding)
    if os.getenv("ANTHROPIC_API_KEY"):
        try:
            return get_model("anthropic:claude-sonnet-4-5-20250929", temperature=0)
        except Exception:
            print("⚠️  Claude unavailable, falling back to Gemini")

    # Fallback to Gemini
    return get_cheap_model()


# Model presets for different agent types
def get_initializer_model() -> BaseChatModel:
    """Get model for Initializer Agent (smart model for planning)"""
    return get_smart_model()


def get_coding_model() -> BaseChatModel:
    """Get model for Coding Agent (smart model for implementation)"""
    return get_smart_model()


def get_test_model() -> BaseChatModel:
    """Get model for Test Agent (cheap model for test generation)"""
    return get_cheap_model()


def get_qa_model() -> BaseChatModel:
    """Get model for QA/Doc Agent (cheap model for review)"""
    return get_cheap_model()


__all__ = [
    "get_model",
    "get_cheap_model",
    "get_smart_model",
    "get_initializer_model",
    "get_coding_model",
    "get_test_model",
    "get_qa_model",
]
