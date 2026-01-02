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
    tokens_per_sec: float
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
    def generate(self, prompt: str, max_tokens: int) -> tuple[int, float, str]:
        """Generate tokens and return (token_count, elapsed_seconds, generated_text)."""
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
        total_tokens = 0
        total_time = 0.0
        per_iteration = []
        sample_output = None

        for i in range(iterations):
            self.log(f"Iteration {i+1}/{iterations}...", end=" ", flush=True)

            try:
                tokens, elapsed, text = self.generate(prompt, max_tokens)
                tps = tokens / elapsed if elapsed > 0 else 0

                self.log(f"{tokens} tokens in {elapsed:.2f}s = {tps:.2f} tok/s")

                total_tokens += tokens
                total_time += elapsed
                per_iteration.append({
                    "tokens": tokens,
                    "elapsed": elapsed,
                    "tokens_per_sec": tps,
                    "text": text[:200] if text else None,  # Store truncated text
                })

                # Keep first successful output as sample
                if sample_output is None and text:
                    sample_output = text
            except Exception as e:
                self.log(f"error: {e}")
                per_iteration.append({"error": str(e)})

        # Calculate averages
        avg_tps = total_tokens / total_time if total_time > 0 else 0

        # Unload and cleanup
        self.unload()
        self.cleanup_memory()

        return BenchResult(
            name=self.model_name,
            engine=self.engine_name,
            tokens_per_sec=avg_tps,
            total_tokens=total_tokens,
            elapsed_sec=total_time,
            quantization=info.get("quantization", "unknown"),
            model_size_gb=info.get("size_gb"),
            ram_gb=info.get("ram_gb"),
            vram_gb=info.get("vram_gb"),
            iterations=iterations,
            per_iteration=per_iteration,
            sample_output=sample_output,
        )
