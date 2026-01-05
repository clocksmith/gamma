"""Base runner class for benchmarks."""

import gc
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class BenchResult:
    """Result from a benchmark run."""

    name: str
    engine: str
    tokens_per_sec: float  # Overall average (decode) tokens per second
    total_tokens: int
    elapsed_sec: float
    quantization: str
    model_size_gb: float | None = None
    ram_gb: float | None = None
    vram_gb: float | None = None
    iterations: int = 0
    per_iteration: list[dict] = field(default_factory=list)
    error: str | None = None
    sample_output: str | None = None  # Sample of generated text for validation
    # Granular timing metrics
    prefill_tokens_per_sec: float | None = None  # Prefill (prompt processing) speed
    decode_tokens_per_sec: float | None = None   # Decode (generation) speed
    ttft_ms: float | None = None                 # Time to first token in milliseconds
    prefill_tokens: int | None = None            # Number of prefill (prompt) tokens
    decode_tokens: int | None = None             # Number of decode (generated) tokens


class BaseRunner(ABC):
    """Base class for benchmark runners."""

    engine_name: str = "base"

    def __init__(self, model_name: str, device: str = "auto", verbose: bool = True):
        self.model_name = model_name
        self.device = device
        self.verbose = verbose
        self._model = None
        self._tokenizer = None

    def log(self, msg: str, end: str = "\n", flush: bool = False):
        """Print if verbose mode is enabled."""
        if self.verbose:
            print(msg, end=end, flush=flush)

    @abstractmethod
    def get_model_info(self) -> dict:
        """Get model info including quantization and size.

        Returns:
            dict with keys: quantization, size_gb, params (optional)
        """
        pass

    @abstractmethod
    def load(self) -> None:
        """Load the model into memory."""
        pass

    @abstractmethod
    def unload(self) -> None:
        """Unload the model and free memory."""
        pass

    @abstractmethod
    def generate(self, prompt: str, max_tokens: int) -> dict:
        """Generate tokens and return metrics dict.

        Returns:
            dict with keys:
                - decode_tokens: int - number of generated tokens
                - decode_time_sec: float - time spent decoding
                - text: str - generated text
                - prefill_tokens: int (optional) - number of prompt tokens
                - prefill_time_sec: float (optional) - time spent on prefill
                - ttft_sec: float (optional) - time to first token
        """
        pass

    def warmup(self, prompt: str = "Hello", max_tokens: int = 10) -> None:
        """Warm up the model with a short generation."""
        self.log("Warmup...", end=" ", flush=True)
        try:
            self.generate(prompt, max_tokens)
            self.log("done")
        except Exception as e:
            self.log(f"warmup failed: {e}")

    def cleanup_memory(self) -> None:
        """Force garbage collection and clear caches."""
        gc.collect()

        # Try to clear CUDA cache if available
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.synchronize()
        except ImportError:
            pass

    def run(
        self,
        prompt: str,
        max_tokens: int = 100,
        iterations: int = 3,
        warmup: bool = True,
    ) -> BenchResult:
        """Run the full benchmark.

        Args:
            prompt: The prompt to generate from
            max_tokens: Max tokens to generate per iteration
            iterations: Number of iterations to run
            warmup: Whether to run warmup before benchmarking

        Returns:
            BenchResult with aggregated metrics
        """
        self.log(f"\n{'='*60}")
        self.log(f"Benchmarking {self.engine_name}: {self.model_name}")
        self.log(f"{'='*60}")

        # Get model info
        info = self.get_model_info()
        self.log(f"Quantization: {info.get('quantization', 'unknown')}")
        if info.get("size_gb"):
            self.log(f"Model size: {info['size_gb']:.1f} GB")
        if info.get("params"):
            self.log(f"Parameters: {info['params']}")

        # Load model
        try:
            self.load()
        except Exception as e:
            return BenchResult(
                name=self.model_name,
                engine=self.engine_name,
                tokens_per_sec=0,
                total_tokens=0,
                elapsed_sec=0,
                quantization=info.get("quantization", "unknown"),
                error=str(e),
            )

        # Refresh model info after load (may have more details now)
        info = self.get_model_info()

        # Warmup
        if warmup:
            self.warmup(prompt, max_tokens=10)

        # Run iterations
        total_decode_tokens = 0
        total_decode_time = 0.0
        total_prefill_tokens = 0
        total_prefill_time = 0.0
        total_ttft = 0.0
        ttft_count = 0
        per_iteration = []
        sample_output = None

        for i in range(iterations):
            self.log(f"Iteration {i+1}/{iterations}...", end=" ", flush=True)

            try:
                result = self.generate(prompt, max_tokens)

                decode_tokens = result.get("decode_tokens", 0)
                decode_time = result.get("decode_time_sec", 0)
                text = result.get("text", "")
                prefill_tokens = result.get("prefill_tokens")
                prefill_time = result.get("prefill_time_sec")
                ttft = result.get("ttft_sec")

                decode_tps = decode_tokens / decode_time if decode_time > 0 else 0
                prefill_tps = prefill_tokens / prefill_time if prefill_time and prefill_time > 0 else None

                # Log with prefill info if available
                if prefill_tps is not None:
                    self.log(f"{decode_tokens} tok in {decode_time:.2f}s = {decode_tps:.1f} tok/s (prefill: {prefill_tps:.1f} tok/s)")
                else:
                    self.log(f"{decode_tokens} tok in {decode_time:.2f}s = {decode_tps:.1f} tok/s")

                total_decode_tokens += decode_tokens
                total_decode_time += decode_time

                if prefill_tokens is not None:
                    total_prefill_tokens += prefill_tokens
                if prefill_time is not None:
                    total_prefill_time += prefill_time
                if ttft is not None:
                    total_ttft += ttft
                    ttft_count += 1

                iter_data = {
                    "decode_tokens": decode_tokens,
                    "decode_time_sec": decode_time,
                    "decode_tokens_per_sec": decode_tps,
                    "text": text[:200] if text else None,
                }
                if prefill_tokens is not None:
                    iter_data["prefill_tokens"] = prefill_tokens
                if prefill_time is not None:
                    iter_data["prefill_time_sec"] = prefill_time
                if prefill_tps is not None:
                    iter_data["prefill_tokens_per_sec"] = prefill_tps
                if ttft is not None:
                    iter_data["ttft_sec"] = ttft

                per_iteration.append(iter_data)

                # Keep first successful output as sample
                if sample_output is None and text:
                    sample_output = text
            except Exception as e:
                self.log(f"error: {e}")
                per_iteration.append({"error": str(e)})

        # Calculate averages
        avg_decode_tps = total_decode_tokens / total_decode_time if total_decode_time > 0 else 0
        avg_prefill_tps = total_prefill_tokens / total_prefill_time if total_prefill_time > 0 else None
        avg_ttft_ms = (total_ttft / ttft_count * 1000) if ttft_count > 0 else None

        # Unload and cleanup
        self.unload()
        self.cleanup_memory()

        return BenchResult(
            name=self.model_name,
            engine=self.engine_name,
            tokens_per_sec=avg_decode_tps,
            total_tokens=total_decode_tokens,
            elapsed_sec=total_decode_time,
            quantization=info.get("quantization", "unknown"),
            model_size_gb=info.get("size_gb"),
            ram_gb=info.get("ram_gb"),
            vram_gb=info.get("vram_gb"),
            iterations=iterations,
            per_iteration=per_iteration,
            sample_output=sample_output,
            # New granular metrics
            prefill_tokens_per_sec=avg_prefill_tps,
            decode_tokens_per_sec=avg_decode_tps,
            ttft_ms=avg_ttft_ms,
            prefill_tokens=total_prefill_tokens if total_prefill_tokens > 0 else None,
            decode_tokens=total_decode_tokens if total_decode_tokens > 0 else None,
        )
