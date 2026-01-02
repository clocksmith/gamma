"""vLLM benchmark runner."""

import time

from .base import BaseRunner


class VLLMRunner(BaseRunner):
    """Runner for vLLM models."""

    engine_name = "vLLM"

    def __init__(
        self,
        model_name: str,
        device: str = "auto",
        quantization: str | None = None,
        tensor_parallel_size: int = 1,
        gpu_memory_utilization: float = 0.9,
        dtype: str = "auto",
        verbose: bool = True,
    ):
        super().__init__(model_name, device, verbose)
        self.quantization = quantization
        self.tensor_parallel_size = tensor_parallel_size
        self.gpu_memory_utilization = gpu_memory_utilization
        self.dtype = dtype
        self._vram_gb: float | None = None
        self._detected_quant: str | None = None

    def get_model_info(self) -> dict:
        """Get model info."""
        quant = self._detected_quant or self.quantization or self.dtype
        if quant == "auto":
            quant = "auto (fp16/bf16)"

        return {
            "quantization": quant.upper() if quant else "FP16",
            "size_gb": None,  # vLLM doesn't expose this easily
            "vram_gb": self._vram_gb,
            "tensor_parallel": self.tensor_parallel_size,
        }

    def load(self) -> None:
        """Load model with vLLM."""
        try:
            from vllm import LLM, SamplingParams
        except ImportError:
            raise RuntimeError("vLLM not installed. Install with: pip install vllm")

        self.log("Loading model with vLLM...")
        load_start = time.perf_counter()

        # Build engine args
        engine_kwargs = {
            "model": self.model_name,
            "tensor_parallel_size": self.tensor_parallel_size,
            "gpu_memory_utilization": self.gpu_memory_utilization,
            "dtype": self.dtype,
            "trust_remote_code": True,
        }

        # Add quantization if specified
        if self.quantization:
            engine_kwargs["quantization"] = self.quantization
            self.log(f"Using {self.quantization.upper()} quantization")

        self._model = LLM(**engine_kwargs)
        self._sampling_params_class = SamplingParams

        load_time = time.perf_counter() - load_start
        self.log(f"Model loaded in {load_time:.1f}s")

        # Detect quantization from model config
        try:
            model_config = self._model.llm_engine.model_config
            if hasattr(model_config, "quantization"):
                self._detected_quant = model_config.quantization
            elif hasattr(model_config, "dtype"):
                self._detected_quant = str(model_config.dtype)
        except Exception:
            pass

        if self._detected_quant:
            self.log(f"Detected quantization: {self._detected_quant}")

        # Get VRAM usage
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.synchronize()
                self._vram_gb = torch.cuda.memory_allocated() / (1024**3)
                self.log(f"VRAM allocated: {self._vram_gb:.2f} GB")
        except ImportError:
            pass

    def unload(self) -> None:
        """Unload model and free memory."""
        if self._model is not None:
            del self._model
            self._model = None

        # Clear CUDA cache
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.synchronize()
        except ImportError:
            pass

    def generate(self, prompt: str, max_tokens: int) -> tuple[int, float, str]:
        """Generate tokens using vLLM."""
        if self._model is None:
            raise RuntimeError("Model not loaded")

        sampling_params = self._sampling_params_class(
            max_tokens=max_tokens,
            temperature=0,  # Greedy for deterministic benchmarking
        )

        start = time.perf_counter()
        outputs = self._model.generate([prompt], sampling_params)
        elapsed = time.perf_counter() - start

        # Count generated tokens and get text
        output = outputs[0]
        num_tokens = len(output.outputs[0].token_ids)
        generated_text = output.outputs[0].text

        return num_tokens, elapsed, generated_text
