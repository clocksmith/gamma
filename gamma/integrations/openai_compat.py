"""
OpenAI API compatibility layer for GAMMA engines.

Allows GAMMA engines to be used with OpenAI-compatible request/response formats.
Supports:
- Chat completions (messages format)
- Text completions (prompt format)
- Streaming responses
- Function calling (basic support)
"""
from typing import Dict, Any, List, Optional, Iterator, Union
import time
import uuid
from dataclasses import dataclass, asdict


@dataclass
class OpenAIMessage:
    """Represents a message in OpenAI chat format."""
    role: str  # "system", "user", "assistant", "function"
    content: str
    name: Optional[str] = None
    function_call: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {"role": self.role, "content": self.content}
        if self.name:
            result["name"] = self.name
        if self.function_call:
            result["function_call"] = self.function_call
        return result


@dataclass
class OpenAIChoice:
    """Represents a choice in OpenAI response."""
    index: int
    message: Optional[OpenAIMessage] = None
    text: Optional[str] = None
    finish_reason: str = "stop"  # "stop", "length", "function_call", "content_filter"
    logprobs: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "index": self.index,
            "finish_reason": self.finish_reason
        }
        if self.message:
            result["message"] = self.message.to_dict()
        if self.text is not None:
            result["text"] = self.text
        if self.logprobs:
            result["logprobs"] = self.logprobs
        return result


@dataclass
class OpenAIUsage:
    """Token usage statistics."""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class OpenAIResponse:
    """OpenAI-compatible response."""
    id: str
    object: str  # "chat.completion" or "text_completion"
    created: int
    model: str
    choices: List[OpenAIChoice]
    usage: OpenAIUsage

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "object": self.object,
            "created": self.created,
            "model": self.model,
            "choices": [choice.to_dict() for choice in self.choices],
            "usage": self.usage.to_dict()
        }


class OpenAICompatibleEngine:
    """
    Wrapper that makes any GAMMA engine OpenAI-compatible.

    Example:
        engine = PyTorchEngine("gpt2")
        engine.load()

        compat_engine = OpenAICompatibleEngine(engine)

        response = compat_engine.chat_completion(
            messages=[
                {"role": "user", "content": "Hello!"}
            ],
            max_tokens=50
        )
    """

    def __init__(self, engine: Any):
        """
        Initialize with a GAMMA engine.

        Args:
            engine: Any GAMMA engine instance (must have encode, predict_next, decode)
        """
        self.engine = engine
        self.model_name = getattr(engine, 'model_name', 'unknown')

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 100,
        temperature: float = 0.7,
        top_p: float = 0.9,
        top_k: int = 50,
        n: int = 1,
        stop: Optional[List[str]] = None,
        stream: bool = False,
        **kwargs
    ) -> Union[Dict[str, Any], Iterator[Dict[str, Any]]]:
        """
        Generate chat completion in OpenAI format.

        Args:
            messages: List of message dicts with "role" and "content"
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Nucleus sampling threshold
            top_k: Top-k sampling
            n: Number of completions (currently only supports 1)
            stop: Stop sequences
            stream: Whether to stream responses
            **kwargs: Additional engine-specific parameters

        Returns:
            OpenAI-formatted response dict or iterator of chunks if streaming
        """
        if n > 1:
            raise NotImplementedError("Multiple completions (n > 1) not yet supported")

        if stream:
            return self._stream_chat_completion(
                messages, max_tokens, temperature, top_p, top_k, stop, **kwargs
            )

        # Convert messages to prompt
        prompt = self._messages_to_prompt(messages)

        # Generate completion
        generated_text, prompt_tokens, completion_tokens = self._generate(
            prompt, max_tokens, temperature, top_p, top_k, stop
        )

        # Build response
        response = OpenAIResponse(
            id=f"chatcmpl-{uuid.uuid4().hex[:8]}",
            object="chat.completion",
            created=int(time.time()),
            model=self.model_name,
            choices=[
                OpenAIChoice(
                    index=0,
                    message=OpenAIMessage(role="assistant", content=generated_text),
                    finish_reason="stop"
                )
            ],
            usage=OpenAIUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens
            )
        )

        return response.to_dict()

    def completion(
        self,
        prompt: str,
        max_tokens: int = 100,
        temperature: float = 0.7,
        top_p: float = 0.9,
        top_k: int = 50,
        n: int = 1,
        stop: Optional[List[str]] = None,
        stream: bool = False,
        echo: bool = False,
        logprobs: Optional[int] = None,
        **kwargs
    ) -> Union[Dict[str, Any], Iterator[Dict[str, Any]]]:
        """
        Generate text completion in OpenAI format.

        Args:
            prompt: Text prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Nucleus sampling threshold
            top_k: Top-k sampling
            n: Number of completions
            stop: Stop sequences
            stream: Whether to stream responses
            echo: Whether to echo the prompt
            logprobs: Include log probabilities
            **kwargs: Additional engine-specific parameters

        Returns:
            OpenAI-formatted response dict or iterator of chunks if streaming
        """
        if n > 1:
            raise NotImplementedError("Multiple completions (n > 1) not yet supported")

        if stream:
            return self._stream_completion(
                prompt, max_tokens, temperature, top_p, top_k, stop, echo, **kwargs
            )

        # Generate completion
        generated_text, prompt_tokens, completion_tokens = self._generate(
            prompt, max_tokens, temperature, top_p, top_k, stop
        )

        # Optionally echo prompt
        if echo:
            generated_text = prompt + generated_text

        # Build response
        response = OpenAIResponse(
            id=f"cmpl-{uuid.uuid4().hex[:8]}",
            object="text_completion",
            created=int(time.time()),
            model=self.model_name,
            choices=[
                OpenAIChoice(
                    index=0,
                    text=generated_text,
                    finish_reason="stop"
                )
            ],
            usage=OpenAIUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens
            )
        )

        return response.to_dict()

    def _generate(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
        top_p: float,
        top_k: int,
        stop: Optional[List[str]] = None
    ) -> tuple[str, int, int]:
        """
        Internal generation method using GAMMA engine.

        Returns:
            Tuple of (generated_text, prompt_tokens, completion_tokens)
        """
        # Encode prompt
        input_ids, attention_mask = self.engine.encode(prompt)
        prompt_tokens = len(input_ids[0]) if len(input_ids.shape) > 1 else len(input_ids)

        # Generate tokens
        generated_tokens = []
        current_input_ids = input_ids
        current_attention_mask = attention_mask

        for _ in range(max_tokens):
            # Predict next token
            output = self.engine.predict_next(
                current_input_ids,
                current_attention_mask,
                temperature=temperature,
                top_k=top_k,
                top_p=top_p
            )

            next_token_id = output["next_token_id"]
            generated_tokens.append(next_token_id)

            # Check for EOS token
            if hasattr(self.engine, 'tokenizer') and hasattr(self.engine.tokenizer, 'eos_token_id'):
                if next_token_id == self.engine.tokenizer.eos_token_id:
                    break

            # Update input for next iteration
            current_input_ids = output.get("input_ids_updated", current_input_ids)
            current_attention_mask = output.get("attention_mask_updated", current_attention_mask)

            # Check stop sequences
            if stop:
                partial_text = self.engine.decode(generated_tokens)
                if any(stop_seq in partial_text for stop_seq in stop):
                    break

        # Decode generated tokens
        generated_text = self.engine.decode(generated_tokens)

        # Remove stop sequences from end
        if stop:
            for stop_seq in stop:
                if generated_text.endswith(stop_seq):
                    generated_text = generated_text[:-len(stop_seq)]

        completion_tokens = len(generated_tokens)

        return generated_text, prompt_tokens, completion_tokens

    def _stream_chat_completion(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int,
        temperature: float,
        top_p: float,
        top_k: int,
        stop: Optional[List[str]],
        **kwargs
    ) -> Iterator[Dict[str, Any]]:
        """Stream chat completion chunks."""
        prompt = self._messages_to_prompt(messages)

        for chunk in self._stream_generation(prompt, max_tokens, temperature, top_p, top_k, stop):
            yield {
                "id": f"chatcmpl-{uuid.uuid4().hex[:8]}",
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": self.model_name,
                "choices": [
                    {
                        "index": 0,
                        "delta": {"role": "assistant", "content": chunk},
                        "finish_reason": None
                    }
                ]
            }

        # Final chunk
        yield {
            "id": f"chatcmpl-{uuid.uuid4().hex[:8]}",
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": self.model_name,
            "choices": [
                {
                    "index": 0,
                    "delta": {},
                    "finish_reason": "stop"
                }
            ]
        }

    def _stream_completion(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
        top_p: float,
        top_k: int,
        stop: Optional[List[str]],
        echo: bool,
        **kwargs
    ) -> Iterator[Dict[str, Any]]:
        """Stream text completion chunks."""
        if echo:
            # Echo prompt first
            yield {
                "id": f"cmpl-{uuid.uuid4().hex[:8]}",
                "object": "text_completion",
                "created": int(time.time()),
                "model": self.model_name,
                "choices": [
                    {
                        "index": 0,
                        "text": prompt,
                        "finish_reason": None
                    }
                ]
            }

        for chunk in self._stream_generation(prompt, max_tokens, temperature, top_p, top_k, stop):
            yield {
                "id": f"cmpl-{uuid.uuid4().hex[:8]}",
                "object": "text_completion",
                "created": int(time.time()),
                "model": self.model_name,
                "choices": [
                    {
                        "index": 0,
                        "text": chunk,
                        "finish_reason": None
                    }
                ]
            }

        # Final chunk
        yield {
            "id": f"cmpl-{uuid.uuid4().hex[:8]}",
            "object": "text_completion",
            "created": int(time.time()),
            "model": self.model_name,
            "choices": [
                {
                    "index": 0,
                    "text": "",
                    "finish_reason": "stop"
                }
            ]
        }

    def _stream_generation(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
        top_p: float,
        top_k: int,
        stop: Optional[List[str]]
    ) -> Iterator[str]:
        """Stream individual token generation."""
        input_ids, attention_mask = self.engine.encode(prompt)

        current_input_ids = input_ids
        current_attention_mask = attention_mask

        for _ in range(max_tokens):
            output = self.engine.predict_next(
                current_input_ids,
                current_attention_mask,
                temperature=temperature,
                top_k=top_k,
                top_p=top_p
            )

            next_token_id = output["next_token_id"]

            # Check for EOS
            if hasattr(self.engine, 'tokenizer') and hasattr(self.engine.tokenizer, 'eos_token_id'):
                if next_token_id == self.engine.tokenizer.eos_token_id:
                    break

            # Decode token
            token_text = self.engine.decode([next_token_id])

            # Check stop sequences
            if stop and any(stop_seq in token_text for stop_seq in stop):
                break

            yield token_text

            # Update input
            current_input_ids = output.get("input_ids_updated", current_input_ids)
            current_attention_mask = output.get("attention_mask_updated", current_attention_mask)

    def _messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        """
        Convert OpenAI messages format to a single prompt string.

        Uses a simple template. Can be customized for specific chat models.
        """
        prompt_parts = []

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                prompt_parts.append(f"System: {content}")
            elif role == "user":
                prompt_parts.append(f"User: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
            elif role == "function":
                name = msg.get("name", "function")
                prompt_parts.append(f"Function {name}: {content}")

        # Add final assistant prompt
        prompt_parts.append("Assistant:")

        return "\n\n".join(prompt_parts)


# Convenience functions

def create_openai_compatible_engine(engine: Any) -> OpenAICompatibleEngine:
    """
    Create an OpenAI-compatible wrapper for any GAMMA engine.

    Args:
        engine: GAMMA engine instance

    Returns:
        OpenAICompatibleEngine wrapper
    """
    return OpenAICompatibleEngine(engine)


def messages_to_prompt(messages: List[Dict[str, str]], template: str = "default") -> str:
    """
    Convert messages to prompt using various templates.

    Args:
        messages: List of message dicts
        template: Template style ("default", "llama2", "chatml", "alpaca")

    Returns:
        Formatted prompt string
    """
    if template == "default":
        return OpenAICompatibleEngine(None)._messages_to_prompt(messages)

    elif template == "llama2":
        # Llama 2 chat format
        prompt_parts = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                prompt_parts.append(f"<<SYS>>\n{content}\n<</SYS>>")
            elif role == "user":
                prompt_parts.append(f"[INST] {content} [/INST]")
            elif role == "assistant":
                prompt_parts.append(f"{content}")

        return " ".join(prompt_parts)

    elif template == "chatml":
        # ChatML format (used by GPT-4, Mistral, etc.)
        prompt_parts = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            prompt_parts.append(f"<|im_start|>{role}\n{content}<|im_end|>")

        prompt_parts.append("<|im_start|>assistant\n")
        return "\n".join(prompt_parts)

    elif template == "alpaca":
        # Alpaca instruction format
        system_msg = ""
        instruction = ""
        input_text = ""

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                system_msg = content
            elif role == "user":
                if not instruction:
                    instruction = content
                else:
                    input_text += content + "\n"

        prompt = f"Below is an instruction that describes a task."
        if input_text:
            prompt += " Below is an input that provides further context."
        prompt += "\n\n"
        prompt += f"### Instruction:\n{instruction}\n\n"
        if input_text:
            prompt += f"### Input:\n{input_text}\n\n"
        prompt += "### Response:\n"

        return prompt

    else:
        raise ValueError(f"Unknown template: {template}")
