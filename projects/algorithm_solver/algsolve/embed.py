"""Qwen3-Embedding-0.6B encoder, read in place from the hash-verified copy.

The weights are Doppler's local copy; their sha256 matched the Hugging Face
release (model.safetensors 0437e45c..., tokenizer.json def76fb0...). They are
read, never copied or modified.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

import numpy as np

# Override with ALGSOLVE_EMBEDDING_DIR on another machine (e.g. a Hugging Face snapshot of
# Qwen/Qwen3-Embedding-0.6B); the sha256 check below still applies.
EMBEDDING_DIR = Path(os.environ.get(
    "ALGSOLVE_EMBEDDING_DIR",
    "/home/x/.local/share/doppler/capsule-baselines/20260906/source-checkpoints/qwen-embedding-source-97b0c614",
))
EXPECTED_SHA256 = {
    "model.safetensors": "0437e45c94563b09e13cb7a64478fc406947a93cb34a7e05870fc8dcd48e23fd",
    "tokenizer.json": "def76fb086971c7867b829c23a26261e38d9d74e02139253b38aeb9df8b4b50a",
}
QUERY_INSTRUCTION = "Instruct: Given a programming problem, retrieve the identical problem\nQuery: "
MAX_TOKENS = 1024


class LazyCPUEmbedder:
    """Retain the encoder once needed; exact lookup can run without loading it."""
    def __init__(self):
        self.encoder = None

    def encode(self, *args, **kwargs):
        if self.encoder is None:
            import torch
            torch.set_num_threads(4)
            self.encoder = Embedder(device='cpu')
        return self.encoder.encode(*args, **kwargs)


def verify_weights() -> None:
    for name, expected in EXPECTED_SHA256.items():
        digest = hashlib.sha256()
        with (EMBEDDING_DIR / name).open("rb") as handle:
            for chunk in iter(lambda: handle.read(1 << 22), b""):
                digest.update(chunk)
        if digest.hexdigest() != expected:
            raise RuntimeError(f"embedding weights changed: {name}")


class Embedder:
    def __init__(self, device: str | None = None) -> None:
        device = device or os.environ.get("ALGSOLVE_DEVICE", "cuda")
        import torch
        from transformers import AutoModel, AutoTokenizer

        verify_weights()
        self.torch = torch
        self.device = device
        self.tokenizer = AutoTokenizer.from_pretrained(EMBEDDING_DIR, padding_side="left")
        dtype = torch.float16 if device != "cpu" else torch.float32
        self.model = AutoModel.from_pretrained(EMBEDDING_DIR, dtype=dtype).to(device).eval()

    def encode(self, texts: list[str], *, query: bool = False, instruction: str | None = None,
               batch_size: int = 16) -> np.ndarray:
        torch = self.torch
        prefix = (instruction or QUERY_INSTRUCTION) if query else ""
        out = []
        for start in range(0, len(texts), batch_size):
            batch = [prefix + t for t in texts[start:start + batch_size]]
            enc = self.tokenizer(batch, padding=True, truncation=True, max_length=MAX_TOKENS, return_tensors="pt").to(self.device)
            with torch.no_grad():
                hidden = self.model(**enc).last_hidden_state
            # Left padding: the last position is each sequence's final token.
            pooled = hidden[:, -1]
            pooled = torch.nn.functional.normalize(pooled.float(), dim=-1)
            out.append(pooled.cpu().numpy())
        return np.concatenate(out) if out else np.zeros((0, 1024), dtype=np.float32)
