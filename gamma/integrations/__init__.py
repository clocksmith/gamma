"""Integration modules for GAMMA with external frameworks."""
from .openai_compat import (
    OpenAICompatibleEngine,
    create_openai_compatible_engine,
    messages_to_prompt
)

try:
    from .langchain_compat import (
        GAMMALangChainLLM,
        GAMMAEmbeddings,
        create_langchain_llm,
        create_langchain_embeddings
    )
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

from .ecosystem_utils import (
    get_available_frameworks,
    print_available_frameworks,
    suggest_framework_for_model,
    get_recommended_engine_for_model,
    suggest_optimizations,
    compare_frameworks
)

__all__ = [
    "OpenAICompatibleEngine",
    "create_openai_compatible_engine",
    "messages_to_prompt",
    "get_available_frameworks",
    "print_available_frameworks",
    "suggest_framework_for_model",
    "get_recommended_engine_for_model",
    "suggest_optimizations",
    "compare_frameworks"
]

if LANGCHAIN_AVAILABLE:
    __all__.extend([
        "GAMMALangChainLLM",
        "GAMMAEmbeddings",
        "create_langchain_llm",
        "create_langchain_embeddings"
    ])
