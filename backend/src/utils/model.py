"""
Model utility for LangChain 1.0 model-agnostic initialization

Uses init_chat_model() pattern from LangChain 1.1.0 (Nov 24, 2025)
for seamless switching between LLM providers.

Supported providers:
- Google GenAI (Gemini 2.0 Flash) - Default
- Anthropic (Claude Sonnet 4.5)
- OpenAI (GPT-4o)
- OpenRouter (Free models: Mistral, Llama, etc.)
- Sambanova (OSS models)
"""

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI
from langchain.chat_models import init_chat_model
import os
from typing import Optional

# Optional: Sambanova support (requires langchain_sambanova package)
try:
    from langchain_sambanova import ChatSambaNova
    os.environ["SAMBANOVA_API_KEY"] = "c2b461cc-a24d-4eb2-a537-08f13f9dea1c"
    SAMBANOVA_AVAILABLE = True
    llm = ChatSambaNova(
        model="gpt-oss-120b",
        max_tokens=8192,
        temperature=0.1,
    )
except ImportError:
    SAMBANOVA_AVAILABLE = False
    llm = None

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
        - "gemini-2.5-pro" -> inferred as "google_genai:gemini-2.5-pro"
        - "gpt-4o" -> inferred as "openai:gpt-4o"
    """
    model_name = model_override or os.getenv(
        "DEFAULT_MODEL",
        "google_genai:gemini-2.5-flash-lite"
    )

    try:
        # LangChain 1.0 pattern: init_chat_model() automatically infers provider
        return init_chat_model(model_name, temperature=temperature)
    except Exception as e:
        print(f"[WARN]  Failed to initialize {model_name}: {e}")
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
    return get_model(temperature=1)


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
            print("[WARN]  Claude unavailable, falling back to Gemini")

    # Fallback to Gemini
    return get_cheap_model()

def get_sambanova_model() -> BaseChatModel:
    """
    Get Sambanova model for complex tasks (e.g., coding, reasoning)

    Requires langchain_sambanova package to be installed.
    Falls back to Gemini if not available.
    """
    if not SAMBANOVA_AVAILABLE or llm is None:
        print("[WARN]  Sambanova not available, falling back to Gemini")
        return get_cheap_model()
    return llm


def get_openrouter_model(
    model_name: Optional[str] = None,
    temperature: float = 0
) -> BaseChatModel:
    """
    Get OpenRouter model using OpenAI-compatible API

    OpenRouter provides access to multiple LLM providers including free models.
    It uses an OpenAI-compatible API, so we use ChatOpenAI with custom base_url.

    Args:
        model_name: OpenRouter model name (e.g., "mistralai/mistral-7b-instruct:free")
        temperature: Model temperature (0-1)

    Returns:
        ChatOpenAI instance configured for OpenRouter

    Free models available:
        - mistralai/mistral-7b-instruct:free
        - meta-llama/llama-3.1-8b-instruct:free
        - nousresearch/hermes-3-llama-3.1-405b:free

    Example:
        >>> model = get_openrouter_model("mistralai/mistral-7b-instruct:free")
        >>> result = model.invoke([{"role": "user", "content": "Hello"}])

    Docs:
        https://openrouter.ai/docs/quickstart
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENROUTER_API_KEY not found in environment. "
            "Get your key at https://openrouter.ai/keys"
        )

    # Default to free Mistral model if not specified
    model = model_name or os.getenv(
        "OPENROUTER_MODEL",
        "kwaipilot/kat-coder-pro:free"
    )

    return ChatOpenAI(
        model=model,
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        temperature=temperature,
        max_tokens=8192,
    )


# Model presets for different agent types
def get_initializer_model() -> BaseChatModel:
    """
    Get model for Initializer Agent (planning and feature generation)

    Uses Gemini by default (proven tool calling support).
    Set USE_OPENROUTER=true in .env to test OpenRouter instead.
    """
    use_openrouter = os.getenv("USE_OPENROUTER", "false").lower() == "true"

    if use_openrouter:
        try:
            print("[SYNC] Using OpenRouter for Initializer Agent")
            return get_openrouter_model()
        except ValueError:
            print("[WARN]  OpenRouter not configured, falling back to Gemini")
            return get_cheap_model()

    # Default: Use Gemini (reliable tool calling)
    return get_cheap_model()


def get_coding_model() -> BaseChatModel:
    """
    Get model for Coding Agent (implementation and code generation)

    Uses Gemini by default (proven tool calling support).
    Set USE_OPENROUTER=true in .env to test OpenRouter instead.
    """
    use_openrouter = os.getenv("USE_OPENROUTER", "false").lower() == "true"

    if use_openrouter:
        try:
            return get_openrouter_model()
        except ValueError:
            print("[WARN]  OpenRouter not configured, falling back to Gemini")
            return get_cheap_model()

    return get_cheap_model()


def get_test_model() -> BaseChatModel:
    """
    Get model for Test Agent (test generation and execution)

    Uses Gemini by default (proven tool calling support).
    Set USE_OPENROUTER=true in .env to test OpenRouter instead.
    """
    use_openrouter = os.getenv("USE_OPENROUTER", "false").lower() == "true"

    if use_openrouter:
        try:
            return get_openrouter_model()
        except ValueError:
            print("[WARN]  OpenRouter not configured, falling back to Gemini")
            return get_cheap_model()

    return get_cheap_model()


def get_qa_model() -> BaseChatModel:
    """
    Get model for QA/Doc Agent (quality assurance and documentation)

    Uses Gemini by default (proven tool calling support).
    Set USE_OPENROUTER=true in .env to test OpenRouter instead.
    """
    use_openrouter = os.getenv("USE_OPENROUTER", "false").lower() == "true"

    if use_openrouter:
        try:
            return get_openrouter_model()
        except ValueError:
            print("[WARN]  OpenRouter not configured, falling back to Gemini")
            return get_cheap_model()

    return get_cheap_model()


__all__ = [
    "get_model",
    "get_cheap_model",
    "get_smart_model",
    "get_sambanova_model",
    "get_openrouter_model",
    "get_initializer_model",
    "get_coding_model",
    "get_test_model",
    "get_qa_model",
]
