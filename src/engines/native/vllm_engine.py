import logging
import time
from typing import List, Tuple, Optional, Dict, Any
import numpy as np

try:
    from vllm import LLM, SamplingParams
    from vllm.outputs import RequestOutput
    import torch
except ImportError:
    raise ImportError(
        "vLLM library not found. Install with `pip install -r requirements/vllm.txt`"
    )

logger = logging.getLogger(__name__)

from src.core.engine_interface import LLMEngine
from src.core.types import PredictionResult
from src.core import config as game_config
from src.engines import sampling_utils


class VLLMEngine(LLMEngine):
    """
    High-performance vLLM inference engine with PagedAttention and continuous batching.

    Features:
    - Paged Attention for efficient KV cache management
    - Continuous batching for high throughput
    - Optimized CUDA kernels
    - Compatible with HuggingFace models
    """

    def __init__(self, model_name: str, engine_specific_config: Optional[Dict[str, Any]] = None):
        super().__init__(model_name, engine_specific_config)
        self._llm: Optional[LLM] = None
        self._current_prompt: str = ""
        self._prompt_token_ids: List[int] = []

    def load(self):
        """Load model with vLLM optimizations"""
        print(f"VLLMEngine: Initializing vLLM with model '{self.model_name}'...")

        # vLLM configuration
        vllm_kwargs = {
            "model": self.model_name,
            "tensor_parallel_size": self.engine_config.get("vllm_tensor_parallel_size", 1),
            "dtype": self.engine_config.get("vllm_dtype", "auto"),  # auto, float16, bfloat16, float32
            "quantization": self.engine_config.get("vllm_quantization", None),  # awq, gptq, squeezellm, etc.
            "gpu_memory_utilization": self.engine_config.get("vllm_gpu_memory_utilization", 0.9),
            "max_model_len": self.engine_config.get("vllm_max_model_len", None),
            "max_num_seqs": self.engine_config.get("vllm_max_num_seqs", 256),
            "trust_remote_code": self.engine_config.get("trust_remote_code", False),
        }

        # Add download directory if specified
        download_dir = self.engine_config.get("vllm_download_dir", None)
        if download_dir:
            vllm_kwargs["download_dir"] = download_dir

        # Add seed if specified
        seed = self.engine_config.get("seed", None)
        if seed is not None:
            vllm_kwargs["seed"] = seed

        # Remove None values
        vllm_kwargs = {k: v for k, v in vllm_kwargs.items() if v is not None}

        print(f"VLLMEngine: Configuration - Tensor Parallel: {vllm_kwargs.get('tensor_parallel_size', 1)}, "
              f"Dtype: {vllm_kwargs.get('dtype', 'auto')}, "
              f"GPU Memory: {vllm_kwargs.get('gpu_memory_utilization', 0.9):.1%}")

        try:
            self._llm = LLM(**vllm_kwargs)
            print(f"VLLMEngine: Model loaded successfully with vLLM optimizations")
            print(f"  - Paged Attention: Enabled")
            print(f"  - Continuous Batching: Enabled")
            print(f"  - Max sequences: {vllm_kwargs.get('max_num_seqs', 256)}")
        except Exception as e:
            err = f"VLLMEngine: Failed to load model '{self.model_name}': {e}"
            if "CUDA out of memory" in str(e):
                err += "\nHint: Try reducing --vllm-gpu-memory-utilization (default 0.9) or --vllm-max-model-len"
            elif "not found" in str(e).lower():
                err += "\nHint: Check model name/path or use --vllm-download-dir to specify cache location"
            raise RuntimeError(err) from e

        # Get tokenizer from vLLM's internal tokenizer
        self.tokenizer = self._llm.get_tokenizer()
        self._populate_special_token_map()

    def reset_kv_cache(self):
        """vLLM manages KV cache automatically via PagedAttention"""
        # Reset prompt tracking
        self._current_prompt = ""
        self._prompt_token_ids = []
        # vLLM handles KV cache internally, no manual reset needed

    def encode(self, text: str, add_special_tokens: bool = True) -> Tuple[List[int], None]:
        """Encode text using vLLM's tokenizer"""
        if not self.tokenizer:
            raise RuntimeError("VLLMEngine: Tokenizer not loaded.")

        # vLLM's tokenizer is a HuggingFace tokenizer
        token_ids = self.tokenizer.encode(text, add_special_tokens=add_special_tokens)

        # Store for incremental generation
        self._prompt_token_ids = token_ids
        self._current_prompt = text

        return token_ids, None

    def decode(self, token_ids: Any, skip_special_tokens: bool = False) -> str:
        """Decode token IDs to text"""
        if not self.tokenizer:
            raise RuntimeError("VLLMEngine: Tokenizer not loaded.")

        # Convert to list if needed
        if isinstance(token_ids, np.ndarray):
            token_ids = token_ids.tolist()
        elif isinstance(token_ids, torch.Tensor):
            token_ids = token_ids.cpu().tolist()
        elif not isinstance(token_ids, list):
            token_ids = [int(token_ids)]

        return self.tokenizer.decode(token_ids, skip_special_tokens=skip_special_tokens)

    def predict_next(
        self,
        input_ids: Any,
        attention_mask: Any,
        temperature: float,
        top_k: int,
        top_p: float,
        output_attentions: bool = False,
        output_hidden_states: bool = False
    ) -> PredictionResult:
        """
        Predict next token using vLLM.

        Note: vLLM is optimized for batch inference and generation, not single-token prediction.
        This implementation provides compatibility with the GAMMA interface but may not
        fully utilize vLLM's performance benefits for single-token-at-a-time generation.
        """
        if not self._llm:
            raise RuntimeError("VLLMEngine: Model not loaded.")

        start_time = time.time()

        # Convert input_ids to list
        if isinstance(input_ids, torch.Tensor):
            input_ids_list = input_ids.cpu().tolist()
        elif isinstance(input_ids, np.ndarray):
            input_ids_list = input_ids.tolist()
        else:
            input_ids_list = list(input_ids)

        # Flatten if needed (vLLM expects 1D list)
        if isinstance(input_ids_list[0], list):
            input_ids_list = input_ids_list[0]

        # Create sampling params
        # Note: vLLM's SamplingParams are for full generation, but we want logprobs for single token
        sampling_params = SamplingParams(
            n=1,  # Number of sequences to generate
            best_of=1,  # Number of candidates
            temperature=temperature if temperature > 0 else 1.0,  # vLLM doesn't support temp=0
            top_p=top_p if 0 < top_p < 1.0 else 1.0,
            top_k=top_k if top_k > 0 else -1,
            max_tokens=1,  # Generate only 1 token
            logprobs=min(100, game_config.MAX_TOKENS_FOR_PROB_DISPLAY * 2),  # Request logprobs
            skip_special_tokens=False,
        )

        # Use prompt_token_ids for generation (more efficient than text)
        try:
            outputs: List[RequestOutput] = self._llm.generate(
                prompt_token_ids=[input_ids_list],
                sampling_params=sampling_params,
                use_tqdm=False
            )
        except Exception as e:
            raise RuntimeError(f"VLLMEngine: Generation failed: {e}") from e

        if not outputs or len(outputs) == 0:
            raise RuntimeError("VLLMEngine: No output from generation")

        output = outputs[0]

        # Extract the generated token and logprobs
        if not output.outputs or len(output.outputs) == 0:
            raise RuntimeError("VLLMEngine: No completion in output")

        completion = output.outputs[0]
        next_token_id = completion.token_ids[0] if completion.token_ids else 0

        # Get logprobs from vLLM output
        # vLLM returns logprobs for the generated token
        logprobs_dict = completion.logprobs[0] if completion.logprobs else {}

        # Convert vLLM logprobs to our format
        vocab_size = self.get_vocabulary_size()
        logits_raw = np.full(vocab_size, -np.inf, dtype=np.float32)

        # Fill in logprobs for tokens that vLLM returned
        for token_id, logprob_data in logprobs_dict.items():
            if isinstance(logprob_data, dict):
                logprob = logprob_data.get('logprob', -np.inf)
            else:
                logprob = float(logprob_data)

            if 0 <= token_id < vocab_size:
                logits_raw[token_id] = logprob

        # If we have very sparse logprobs, use the common pipeline on what we have
        # but note that this is an approximation since vLLM already did sampling

        # Use common sampling pipeline (for consistency and intermediate values)
        # Note: Since vLLM already sampled, we're reconstructing the pipeline for analysis
        pipeline_results = self._process_logits_common_pipeline(
            logits_raw.copy(), temperature, top_k, top_p
        )

        # Override next_token_id with vLLM's actual choice
        pipeline_results["next_token_id"] = next_token_id

        # Get top tokens from vLLM's logprobs for display
        top_tokens_vllm = []
        top_probs_vllm = []

        # Sort logprobs by value
        sorted_logprobs = sorted(logprobs_dict.items(), key=lambda x: float(x[1].get('logprob', -np.inf) if isinstance(x[1], dict) else x[1]), reverse=True)

        max_display = min(len(sorted_logprobs), game_config.MAX_TOKENS_FOR_PROB_DISPLAY)
        for token_id, logprob_data in sorted_logprobs[:max_display]:
            top_tokens_vllm.append(self.get_token_text(token_id))
            if isinstance(logprob_data, dict):
                prob = np.exp(logprob_data.get('logprob', -np.inf))
            else:
                prob = np.exp(float(logprob_data))
            top_probs_vllm.append(float(prob))

        # Override pipeline's top tokens with vLLM's if available
        if top_tokens_vllm:
            pipeline_results["top_tokens"] = top_tokens_vllm
            pipeline_results["top_probs"] = top_probs_vllm

        inference_time = time.time() - start_time

        logits_processed = pipeline_results["logits_processed_np"]
        logits_after_temperature = pipeline_results["logits_temp_np"]
        logits_after_top_k = pipeline_results["logits_topk_np"]

        return PredictionResult.from_dict({
            "next_token_id": next_token_id,
            "logits_raw": logits_raw,
            "logits_processed": logits_processed,
            "logits_after_temperature": logits_after_temperature,
            "logits_after_top_k": logits_after_top_k,
            "logits_after_top_p": logits_processed,
            "probabilities_raw": sampling_utils.softmax(logits_raw),
            "probabilities_temp": sampling_utils.softmax(logits_after_temperature),
            "probabilities_top_k": sampling_utils.softmax(logits_after_top_k),
            "probabilities_processed": pipeline_results["probs_processed_np"],
            "top_tokens_processed": pipeline_results["top_tokens"],
            "top_probs_processed": pipeline_results["top_probs"],
            "attention": None,  # vLLM doesn't expose attention by default
            "hidden_states": None,  # vLLM doesn't expose hidden states by default
            "forward_time": inference_time,
            "vllm_metadata": {
                "finish_reason": completion.finish_reason,
                "num_tokens_generated": len(completion.token_ids),
            }
        })

    def get_vocabulary_size(self) -> int:
        """Get vocabulary size from tokenizer"""
        if not self.tokenizer:
            raise RuntimeError("VLLMEngine: Tokenizer not loaded.")
        return len(self.tokenizer)

    def _decode_token_raw(self, token_id: int) -> str:
        """Decode a single token ID using vLLM's tokenizer"""
        if not self.tokenizer:
            return f"<token_{token_id}>"

        try:
            # Try to get token text directly
            if hasattr(self.tokenizer, 'convert_ids_to_tokens'):
                token_text = self.tokenizer.convert_ids_to_tokens(token_id)
                if isinstance(token_text, bytes):
                    token_text = token_text.decode("utf-8", errors="replace")
                return token_text if token_text else ""
            else:
                # Fallback to decode
                return self.tokenizer.decode([token_id], skip_special_tokens=False)
        except (KeyError, IndexError, ValueError) as e:
            logger.debug(f"Could not decode token {token_id}: {e}")
            return f"<token_{token_id}>"

    def is_word_like_token(self, token_id: int, txt: Optional[str] = None) -> bool:
        """Check if token is word-like (delegate to base class)"""
        return super().is_word_like_token(token_id, txt)

    def get_probabilities_at_step(
        self, data: Any, s_name: str, k: int
    ) -> Tuple[List[str], List[float], List[int]]:
        """Get top-k probabilities at a given step"""
        if not isinstance(data, np.ndarray):
            raise TypeError(f"Expected np.ndarray for vLLM probabilities, got {type(data)}")

        # Check if already probabilities (sum to ~1.0) or logits
        is_probs = (
            np.all(data >= -1e-6) and
            np.all(data <= 1.0 + 1e-6) and
            np.allclose(np.sum(data, axis=-1), 1.0, atol=1e-3)
        )

        probs_arr = data if is_probs else sampling_utils.softmax(data)
        return sampling_utils.get_top_k_tokens(probs_arr, k, self.get_token_text, is_probs=True)

    def get_config_summary(self) -> Dict[str, Any]:
        """Get configuration summary"""
        if not self._llm:
            return {"Error": "vLLM not loaded"}

        return {
            "Engine": "vLLM",
            "Model": self.model_name,
            "Tensor Parallel Size": self.engine_config.get("vllm_tensor_parallel_size", 1),
            "Dtype": self.engine_config.get("vllm_dtype", "auto"),
            "Quantization": self.engine_config.get("vllm_quantization", "None"),
            "GPU Memory Utilization": f"{self.engine_config.get('vllm_gpu_memory_utilization', 0.9):.1%}",
            "Max Model Length": self.engine_config.get("vllm_max_model_len", "Auto"),
            "Max Sequences": self.engine_config.get("vllm_max_num_seqs", 256),
            "Features": "PagedAttention, Continuous Batching, Optimized CUDA Kernels"
        }

    # Required abstract methods from base class

    def convert_to_numpy(self, tensor: Any) -> np.ndarray:
        """Convert engine-specific tensor to numpy array"""
        if isinstance(tensor, np.ndarray):
            return tensor
        elif isinstance(tensor, torch.Tensor):
            return tensor.cpu().numpy()
        elif isinstance(tensor, list):
            return np.array(tensor)
        else:
            raise TypeError(f"VLLMEngine: Cannot convert {type(tensor)} to numpy array")

    def convert_from_numpy(self, array: np.ndarray) -> Any:
        """Convert numpy array to engine-specific tensor (vLLM uses PyTorch tensors)"""
        if isinstance(array, np.ndarray):
            return torch.from_numpy(array)
        return array

    def concatenate_tensors(self, tensor1: Any, tensor2: Any, dim: int = -1) -> Any:
        """Concatenate two tensors along specified dimension"""
        if tensor1 is None:
            return tensor2
        if tensor2 is None:
            return tensor1

        # Convert to torch tensors if needed
        if not isinstance(tensor1, torch.Tensor):
            tensor1 = torch.tensor(tensor1) if not isinstance(tensor1, np.ndarray) else torch.from_numpy(tensor1)
        if not isinstance(tensor2, torch.Tensor):
            tensor2 = torch.tensor(tensor2) if not isinstance(tensor2, np.ndarray) else torch.from_numpy(tensor2)

        return torch.cat([tensor1, tensor2], dim=dim)

    def get_num_layers(self) -> int:
        """Get the number of layers in the model."""
        if not self._llm:
            raise RuntimeError("VLLMEngine: Model not loaded.")
        try:
            config = self._llm.llm_engine.model_config
            for attr in ('num_hidden_layers', 'n_layer', 'num_layers'):
                if hasattr(config, attr):
                    return getattr(config, attr)
        except (AttributeError, RuntimeError) as e:
            logger.debug(f"Could not get layer count from config: {e}")
        return 32

    def export_kv_cache_state(self) -> Optional[Dict[str, Any]]:
        """Export KV cache state for bridging"""
        # vLLM's PagedAttention manages KV cache internally
        # Provide additional context about PagedAttention
        base_state = super().export_kv_cache_state()
        base_state['note'] = 'vLLM uses PagedAttention - KV cache not directly exportable'
        base_state['paged_attention'] = True
        return base_state

    # KV cache bridge/import: Using default "not supported" implementations from base class

    def append_to_input(self, input_ids: Any, new_token_id: int) -> Any:
        """Append a new token to input_ids"""
        if isinstance(input_ids, list):
            return input_ids + [new_token_id]
        elif isinstance(input_ids, np.ndarray):
            return np.append(input_ids, new_token_id)
        elif isinstance(input_ids, torch.Tensor):
            return torch.cat([input_ids, torch.tensor([new_token_id], device=input_ids.device)])
        else:
            return [new_token_id]

    def get_device(self) -> str:
        """Get device type (vLLM uses CUDA GPUs)"""
        if torch.cuda.is_available():
            return "cuda"
        return "cpu"
