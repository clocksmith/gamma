"""
Wrapper engine implementations for external APIs.

These engines wrap HTTP APIs and other external services. They have limitations:
- Synthetic or approximated logits (not true pre-softmax values)
- Limited or no attention weight access
- No direct access to hidden states
- May have incomplete token probability distributions

Wrapper engines have limited or no Mind Meld compatibility.

NOTE: Engines are imported lazily to avoid dependency errors when not all
engines are installed. Each engine is imported only when needed by the factory.
"""

# Use lazy imports - engines will be imported on-demand by engine_factory.py

__all__ = [
    'OllamaEngine',
    'HuggingFaceInferenceEngine',
    'OpenAIEngine',
]

# Future wrappers:
# - AnthropicWrapper (for Claude API)
# - CohereWrapper (for Cohere API)
# - GoogleAIWrapper (for Gemini API)
# - TogetherAIWrapper (for Together AI API)
