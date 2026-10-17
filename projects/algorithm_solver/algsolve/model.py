"""Qwen3.5-4B generation on the existing transformers/ROCm backend.

One request at a time, greedy decoding, thinking disabled through the chat
template. Each call takes a token cap and a wall-clock cap (max_time); the
result records which one stopped it. Results describe this backend and
configuration only.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass

MODEL_REPO = "Qwen/Qwen3.5-4B"
MODEL_REVISION = "851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a"


@dataclass
class Generation:
    text: str
    prompt_tokens: int
    new_tokens: int
    seconds: float
    stopped_by: str               # eos | max_new_tokens | max_time


class Generator:
    def __init__(self, device: str = "cuda") -> None:
        import torch
        from huggingface_hub import snapshot_download
        from transformers import AutoModelForCausalLM, AutoTokenizer

        self.torch = torch
        path = snapshot_download(MODEL_REPO, revision=MODEL_REVISION, local_files_only=True)
        self.tokenizer = AutoTokenizer.from_pretrained(path)
        self.model = AutoModelForCausalLM.from_pretrained(path, dtype=torch.bfloat16, device_map=device).eval()
        self.device = device
        self.path = path

    def _prompt(self, messages: list[dict]) -> str:
        return self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True, enable_thinking=False
        )

    def generate(self, messages: list[dict], *, max_new_tokens: int, max_time: float) -> Generation:
        torch = self.torch
        if max_time <= 0:
            return Generation("", 0, 0, 0.0, "max_time")
        enc = self.tokenizer(self._prompt(messages), return_tensors="pt").to(self.device)
        prompt_len = enc["input_ids"].shape[1]
        torch.cuda.synchronize()
        started = time.perf_counter()
        with torch.no_grad():
            out = self.model.generate(
                **enc, max_new_tokens=max_new_tokens, max_time=max_time, do_sample=False,
                temperature=None, top_p=None, top_k=None,
            )
        torch.cuda.synchronize()
        seconds = time.perf_counter() - started
        new = out[0, prompt_len:]
        new_tokens = int(new.shape[0])
        eos_ids = self.model.generation_config.eos_token_id
        eos_ids = set(eos_ids if isinstance(eos_ids, list) else [eos_ids])
        if new_tokens and int(new[-1]) in eos_ids:
            stopped = "eos"
        elif new_tokens >= max_new_tokens:
            stopped = "max_new_tokens"
        else:
            stopped = "max_time"
        text = self.tokenizer.decode(new, skip_special_tokens=True)
        return Generation(text, prompt_len, new_tokens, seconds, stopped)

    def generate_batch(self, prompts: list[list[dict]], *, max_new_tokens: int) -> list[str]:
        """Throughput mode for offline data generation (paraphrases); not timed per item."""
        torch = self.torch
        self.tokenizer.padding_side = "left"
        texts = [self._prompt(m) for m in prompts]
        enc = self.tokenizer(texts, return_tensors="pt", padding=True).to(self.device)
        with torch.no_grad():
            out = self.model.generate(**enc, max_new_tokens=max_new_tokens, do_sample=False,
                                      temperature=None, top_p=None, top_k=None)
        return [self.tokenizer.decode(row[enc["input_ids"].shape[1]:], skip_special_tokens=True) for row in out]


_FENCE_RE = re.compile(r"```(?:python|py|python3)?\s*\n(.*?)```", re.S)


def extract_code(text: str) -> str:
    """Take the last fenced Python block; fall back to an unterminated fence or raw text."""
    blocks = _FENCE_RE.findall(text)
    if blocks:
        return blocks[-1].strip() + "\n"
    if "```" in text:
        tail = text.split("```", 1)[1]
        tail = re.sub(r"^(?:python|py|python3)?\s*\n", "", tail)
        return tail.strip() + "\n"
    return text.strip() + "\n"
