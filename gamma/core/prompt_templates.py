"""Shared chat-template detection for the game and Mind Meld."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from gamma.core.engine_interface import LLMEngine


STOP_TEXT_MARKERS = (
    "<end_of_turn>",
    "<|eot_id|>",
    "<|end_of_text|>",
    "<eos>",
    "</s>",
)


def prompt_looks_formatted(prompt: str) -> bool:
    """Detect prompts that already contain a chat role marker."""
    if not prompt:
        return False
    markers = (
        "<|im_start|>",
        "<|assistant|>",
        "[INST]",
        "<<SYS>>",
        "User:",
        "Assistant:",
        "System:",
    )
    return any(marker in prompt for marker in markers)


def should_apply_chat_template(
    engine: LLMEngine | None,
    prompt: str,
    prompt_chat_template: bool | None,
) -> bool:
    """Check explicit preference, template support and model naming."""
    if engine is None or prompt_chat_template is False:
        return False
    tokenizer = getattr(engine, "tokenizer", None)
    if tokenizer is None or not hasattr(tokenizer, "apply_chat_template"):
        return False
    if prompt_chat_template is True:
        return True
    if prompt_looks_formatted(prompt):
        return False
    if getattr(tokenizer, "chat_template", None):
        return True

    model_name = (engine.model_name or "").lower()
    tokenizer_name = getattr(engine.tokenizer, "name_or_path", "")
    combined = f"{model_name} {tokenizer_name}".lower()
    tags = ("-it", "instruct", "instruction", "chat", "assistant")
    return any(tag in combined for tag in tags)
