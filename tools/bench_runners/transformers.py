"""HuggingFace Transformers benchmark runner."""

import time

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, TextStreamer

from .base import BaseRunner


class TTFTStreamer(TextStreamer):
    """Custom streamer that captures time to first token."""

    def __init__(self, tokenizer, start_time: float):
        super().__init__(tokenizer, skip_prompt=True, skip_special_tokens=True)
        self.start_time = start_time
        self.first_token_time: float | None = None
        self.token_count = 0
        self._text_chunks: list[str] = []

    def on_finalized_text(self, text: str, stream_end: bool = False):
        """Called when text is finalized."""
        if self.first_token_time is None and text:
            self.first_token_time = time.perf_counter()
        if text:
            self.token_count += 1
            self._text_chunks.append(text)

    def get_ttft(self) -> float | None:
        """Get time to first token in seconds."""
        if self.first_token_time is not None:
            return self.first_token_time - self.start_time
        return None

    def get_text(self) -> str:
        """Get all generated text."""
        return "".join(self._text_chunks)


class TransformersRunner(BaseRunner):
    """Runner for HuggingFace Transformers models."""

    engine_name = "Transformers"

    # Quantization configs
    QUANT_CONFIGS = {
        "int8": lambda: BitsAndBytesConfig(load_in_8bit=True),
        "int4": lambda: BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16,
        ),
        "nf4": lambda: BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16,
        ),
        "fp4": lambda: BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="fp4",
            bnb_4bit_compute_dtype=torch.bfloat16,
        ),
    }

    def __init__(
        self,
        model_name: str,
        device: str = "auto",
        quantize: str | None = None,
        torch_dtype: str = "bf16",
        verbose: bool = True,
    ):
        super().__init__(model_name, device, verbose)
        self.quantize = quantize
        self.torch_dtype_str = torch_dtype
        self._detected_quant: str | None = None
        self._model_mem_gb: float | None = None
        self._vram_gb: float | None = None

    def _get_torch_dtype(self) -> torch.dtype:
        """Get torch dtype from string."""
        dtype_map = {
            "fp32": torch.float32,
            "fp16": torch.float16,
            "bf16": torch.bfloat16,
        }
        return dtype_map.get(self.torch_dtype_str, torch.bfloat16)

    def get_model_info(self) -> dict:
        """Get model info."""
        info = {
            "quantization": self.quantize or self.torch_dtype_str.upper(),
            "size_gb": self._model_mem_gb,
            "ram_gb": self._model_mem_gb,  # For display in comparison
            "vram_gb": self._vram_gb,
        }

        if self._detected_quant:
            info["quantization"] = self._detected_quant

        return info

    def _detect_quantization(self) -> str:
        """Detect actual quantization method used."""
        if self._model is None:
            return self.quantize or self.torch_dtype_str.upper()

        model = self._model
        config = model.config

        # Check for bitsandbytes quantization
        if hasattr(model, "is_loaded_in_8bit") and model.is_loaded_in_8bit:
            return "INT8 (bnb)"
        if hasattr(model, "is_loaded_in_4bit") and model.is_loaded_in_4bit:
            return "INT4 (bnb)"

        # Check quantization_config
        if hasattr(config, "quantization_config"):
            qconfig = config.quantization_config
            if isinstance(qconfig, dict):
                if qconfig.get("load_in_4bit"):
                    bnb_type = qconfig.get("bnb_4bit_quant_type", "nf4")
                    return f"INT4-{bnb_type}"
                if qconfig.get("load_in_8bit"):
                    return "INT8"
                if "bits" in qconfig:
                    return f"{qconfig['bits']}-bit"

        # Check dtype
        try:
            dtype = next(model.parameters()).dtype
            dtype_map = {
                torch.float32: "FP32",
                torch.float16: "FP16",
                torch.bfloat16: "BF16",
                torch.int8: "INT8",
            }
            return dtype_map.get(dtype, str(dtype))
        except StopIteration:
            return "unknown"

    def _get_model_memory_gb(self) -> float:
        """Calculate model memory usage in GB."""
        if self._model is None:
            return 0.0
        param_bytes = sum(p.numel() * p.element_size() for p in self._model.parameters())
        return param_bytes / (1024**3)

    def load(self) -> None:
        """Load the model and tokenizer."""
        self.log("Loading tokenizer...")
        self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        if self._tokenizer.pad_token is None:
            self._tokenizer.pad_token = self._tokenizer.eos_token

        self.log("Loading model...")
        load_start = time.perf_counter()

        # Build model kwargs
        model_kwargs = {
            "device_map": self.device,
            "torch_dtype": self._get_torch_dtype(),
            "trust_remote_code": True,
        }

        # Add quantization config if specified
        if self.quantize and self.quantize in self.QUANT_CONFIGS:
            model_kwargs["quantization_config"] = self.QUANT_CONFIGS[self.quantize]()
            self.log(f"Using {self.quantize.upper()} quantization")

        self._model = AutoModelForCausalLM.from_pretrained(self.model_name, **model_kwargs)

        load_time = time.perf_counter() - load_start
        self.log(f"Model loaded in {load_time:.1f}s")

        # Detect actual quantization
        self._detected_quant = self._detect_quantization()
        self.log(f"Detected quantization: {self._detected_quant}")

        # Calculate memory usage
        self._model_mem_gb = self._get_model_memory_gb()
        self.log(f"Model memory: {self._model_mem_gb:.2f} GB")

        # Get VRAM if on GPU
        if torch.cuda.is_available():
            torch.cuda.synchronize()
            self._vram_gb = torch.cuda.memory_allocated() / (1024**3)
            self.log(f"VRAM allocated: {self._vram_gb:.2f} GB")

    def unload(self) -> None:
        """Unload model and free memory."""
        if self._model is not None:
            del self._model
            self._model = None

        if self._tokenizer is not None:
            del self._tokenizer
            self._tokenizer = None

        # Clear CUDA cache
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()

    def generate(self, prompt: str, max_tokens: int) -> dict:
        """Generate tokens and measure time with TTFT tracking."""
        if self._model is None or self._tokenizer is None:
            raise RuntimeError("Model not loaded")

        # Tokenize
        inputs = self._tokenizer(prompt, return_tensors="pt").to(self._model.device)
        input_len = inputs.input_ids.shape[1]

        # Sync before timing
        if torch.cuda.is_available():
            torch.cuda.synchronize()

        start = time.perf_counter()

        # Create streamer for TTFT measurement
        streamer = TTFTStreamer(self._tokenizer, start)

        with torch.no_grad():
            outputs = self._model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                do_sample=False,
                pad_token_id=self._tokenizer.pad_token_id,
                streamer=streamer,
            )

        # Sync after generation
        if torch.cuda.is_available():
            torch.cuda.synchronize()

        end = time.perf_counter()
        total_elapsed = end - start
        new_tokens = outputs.shape[1] - input_len

        # Decode output (use streamer text or decode manually)
        generated_text = streamer.get_text() or self._tokenizer.decode(
            outputs[0][input_len:], skip_special_tokens=True
        )

        result = {
            "decode_tokens": new_tokens,
            "decode_time_sec": total_elapsed,
            "text": generated_text,
            "prefill_tokens": input_len,
        }

        # Add TTFT if captured
        ttft = streamer.get_ttft()
        if ttft is not None:
            result["ttft_sec"] = ttft
            result["prefill_time_sec"] = ttft
            # Refine decode time to exclude prefill
            result["decode_time_sec"] = total_elapsed - ttft

        return result
