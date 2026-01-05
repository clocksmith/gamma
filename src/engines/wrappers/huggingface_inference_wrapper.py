"""
HuggingFace Inference API Wrapper

Speed-optimized wrapper for HuggingFace's hosted inference API.
Provides fast inference without local model loading, but NO real logits access.

Limitations:
- Synthetic logits only (not real pre-softmax values)
- No attention weights
- No hidden states
- Not compatible with Mind Meld mode

Ideal for: Fast text generation without needing probability distributions
"""

import time
import os
from typing import List, Tuple, Optional, Dict, Any

try:
    import numpy as np
    import requests
except ImportError:
    raise ImportError("HuggingFace Inference API requires 'numpy' and 'requests'. Install with: pip install numpy requests")

from src.core.engine_interface import LLMEngine
from src.core.types import PredictionResult
from src.engines import sampling_utils


class HuggingFaceInferenceEngine(LLMEngine):
    """Engine for HuggingFace Inference API (hosted models)."""

    @property
    def supports_logits(self) -> bool:
        return False

    @property
    def supports_attention(self) -> bool:
        return False

    @property
    def supports_kv_cache(self) -> bool:
        return False

    def __init__(self, model_name: str, engine_specific_config: Optional[Dict[str, Any]] = None):
        """
        Initialize HuggingFace Inference API engine.

        Args:
            model_name: HuggingFace model ID (e.g., 'meta-llama/Llama-2-7b-chat-hf')
            engine_specific_config: Optional configuration dict with:
                - hf_token: HuggingFace API token (or set HF_TOKEN env var)
                - api_url: Custom API endpoint (default: router.huggingface.co)
                - provider: Specific inference provider (optional)
        """
        super().__init__(model_name=model_name, engine_specific_config=engine_specific_config)

        # Get API token from config or environment
        self.api_token = (
            self.engine_config.get("hf_token") or
            os.environ.get("HF_TOKEN") or
            os.environ.get("HUGGING_FACE_HUB_TOKEN")
        )

        if not self.api_token:
            raise ValueError(
                "HuggingFace Inference API requires an API token. "
                "Set via --hf-token argument or HF_TOKEN environment variable. "
                "Get your token at: https://huggingface.co/settings/tokens"
            )

        # API endpoint
        self.api_url = self.engine_config.get("api_url", "https://router.huggingface.co/v1")
        self.provider = self.engine_config.get("provider", None)  # Optional specific provider

        # Request headers
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }

        # Vocab size estimate (we don't have access to real tokenizer)
        self._vocab_size = 50000  # Typical for most LLMs
        self._token_cache = {}

        # Message history for chat models
        self._message_history = []

    def load(self):
        """Verify API connection and model availability."""
        print(f"HuggingFaceInferenceEngine: Checking API access for '{self.model_name}'...")

        # Test API connection with a simple request
        try:
            # Try a minimal chat completion request
            test_response = requests.post(
                f"{self.api_url}/chat/completions",
                headers=self.headers,
                json={
                    "model": self.model_name,
                    "messages": [{"role": "user", "content": "test"}],
                    "max_tokens": 1,
                    "temperature": 0.1
                },
                timeout=10
            )

            if test_response.status_code == 200:
                print(f"✓ Successfully connected to HuggingFace Inference API")
                print(f"  Model: {self.model_name}")
                print(f"  Endpoint: {self.api_url}")
            elif test_response.status_code == 401:
                raise RuntimeError(
                    "Authentication failed. Invalid HuggingFace API token. "
                    "Get your token at: https://huggingface.co/settings/tokens"
                )
            elif test_response.status_code == 404:
                raise RuntimeError(
                    f"Model '{self.model_name}' not found or not available via Inference API. "
                    f"Check model availability at: https://huggingface.co/{self.model_name}"
                )
            else:
                print(f"Warning: API returned status {test_response.status_code}: {test_response.text}")
                print("Continuing anyway - some models may need special parameters")

        except requests.exceptions.Timeout:
            raise RuntimeError("HuggingFace Inference API request timed out. Check your network connection.")
        except requests.exceptions.ConnectionError:
            raise RuntimeError("Cannot connect to HuggingFace Inference API. Check your network connection.")
        except Exception as e:
            print(f"Warning: API check issue: {e}")
            print("Continuing anyway - API may still work for generation")

    def encode(self, text: str, add_special_tokens: bool = True) -> Tuple[List[int], None]:
        """
        Encode text to token IDs (pseudo-encoding since we don't have real tokenizer).

        Returns:
            Tuple of (token_ids, None) - attention mask is always None
        """
        # Simple word-based pseudo-encoding
        words = text.split()
        token_ids = [hash(word) % self._vocab_size for word in words]
        return token_ids, None

    def decode(self, token_ids: Any, skip_special_tokens: bool = False) -> str:
        """Decode token IDs to text (using cached tokens)."""
        if isinstance(token_ids, list):
            return " ".join(self._token_cache.get(tid, f"<{tid}>") for tid in token_ids)
        return self._token_cache.get(int(token_ids), f"<{token_ids}>")

    def predict_next(
        self,
        input_ids: List[int],
        attention_mask: Any,
        temperature: float,
        top_k: int,
        top_p: float,
        output_attentions: bool = False,
        output_hidden_states: bool = False
    ) -> PredictionResult:
        """
        Predict next token using HuggingFace Inference API.

        Note: This generates synthetic logits as the API only returns text.
        """
        st = time.time()

        # Decode current tokens to text
        current_text = self.decode(input_ids)

        # Build chat message
        messages = [{"role": "user", "content": current_text}]

        # Call HuggingFace Inference API
        try:
            payload = {
                "model": self.model_name,
                "messages": messages,
                "max_tokens": 1,  # Only generate next token
                "temperature": temperature,
                "top_p": top_p,
                "stream": False
            }

            # Add provider if specified
            if self.provider:
                payload["provider"] = self.provider

            response = requests.post(
                f"{self.api_url}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=30
            )

            response.raise_for_status()
            result = response.json()

            # Extract generated text
            if "choices" in result and len(result["choices"]) > 0:
                generated_text = result["choices"][0]["message"]["content"]
            else:
                raise RuntimeError(f"Unexpected API response format: {result}")

            # Extract next token from generated text
            next_token_text = generated_text.strip().split()[0] if generated_text.strip() else ""

            if not next_token_text:
                next_token_text = " "  # Fallback

            # Pseudo-encode the next token
            next_token_id = hash(next_token_text) % self._vocab_size

            # Cache the token for decoding
            self._token_cache[next_token_id] = next_token_text

            # Create synthetic logits (API doesn't expose real logits)
            logits_raw = np.full(self._vocab_size, -10.0, dtype=np.float32)
            logits_raw[next_token_id] = 1.0  # High score for predicted token

            # Add some alternatives
            num_alternatives = min(top_k - 1, 10)
            for i in range(num_alternatives):
                alt_id = (next_token_id + i + 1) % self._vocab_size
                logits_raw[alt_id] = -1.0 - (i * 0.5)

            # Use common sampling pipeline
            pipeline_results = self._process_logits_common_pipeline(
                logits_raw.copy(), temperature, top_k, top_p
            )

            probs_raw = sampling_utils.softmax(logits_raw)

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
                "probabilities_raw": probs_raw,
                "probabilities_temp": sampling_utils.softmax(logits_after_temperature),
                "probabilities_top_k": sampling_utils.softmax(logits_after_top_k),
                "probabilities_processed": pipeline_results["probs_processed_np"],
                "top_tokens_processed": pipeline_results["top_tokens"],
                "top_probs_processed": pipeline_results["top_probs"],
                "attention": None,
                "hidden_states": None,
                "forward_time": time.time() - st
            })

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                raise RuntimeError("HuggingFace Inference API rate limit exceeded. Try again later or upgrade your plan.")
            elif e.response.status_code == 503:
                raise RuntimeError(f"Model '{self.model_name}' is currently loading. Try again in a few moments.")
            else:
                raise RuntimeError(f"HuggingFace Inference API error ({e.response.status_code}): {e.response.text}")
        except Exception as e:
            raise RuntimeError(f"HuggingFace Inference API call failed: {e}")

    def get_vocabulary_size(self) -> int:
        """Return estimated vocabulary size."""
        return self._vocab_size

    def _decode_token_raw(self, token_id: int) -> str:
        """Decode a single token ID."""
        return self._token_cache.get(token_id, f"<token_{token_id}>")

    def reset_kv_cache(self):
        """Reset message history."""
        self._message_history = []

    def get_config_summary(self) -> Dict[str, Any]:
        """Return configuration summary."""
        return {
            "Engine": "HuggingFace Inference API",
            "Model": self.model_name,
            "API Endpoint": self.api_url,
            "Provider": self.provider or "auto",
            "Token": f"{self.api_token[:8]}..." if self.api_token else "None"
        }

    def get_attention_for_visualization(
        self, attention_output: Any, input_ids_for_viz: Any
    ) -> Optional[Tuple[List[str], List[float]]]:
        """Get attention weights - not available via API."""
        return None

    def get_probabilities_at_step(
        self, logits_or_probs: Any, step_name: str, k: int
    ) -> Tuple[List[str], List[float], List[int]]:
        """Get top-k probabilities at a given step."""
        if not isinstance(logits_or_probs, np.ndarray):
            logits_or_probs = np.array(logits_or_probs)

        # Check if it's already probabilities or logits
        is_probs = np.all(logits_or_probs >= 0) and np.allclose(np.sum(logits_or_probs), 1.0, atol=1e-3)
        probs = logits_or_probs if is_probs else sampling_utils.softmax(logits_or_probs)

        # Get top k indices
        top_k_indices = np.argsort(probs)[-k:][::-1]
        top_k_probs = probs[top_k_indices]
        top_k_tokens = [self.get_token_text(idx) for idx in top_k_indices]

        return top_k_tokens, top_k_probs.tolist(), top_k_indices.tolist()

    def convert_to_numpy(self, tensor: Any) -> np.ndarray:
        """Convert engine-specific tensor to numpy array."""
        if isinstance(tensor, np.ndarray):
            return tensor
        elif isinstance(tensor, list):
            return np.array(tensor)
        else:
            raise TypeError(f"HuggingFaceInferenceEngine: Cannot convert {type(tensor)} to numpy array")

    def convert_from_numpy(self, array: np.ndarray) -> Any:
        """Convert numpy array to engine-specific tensor."""
        if isinstance(array, np.ndarray):
            return array.tolist()
        return array

    def concatenate_tensors(self, tensor1: Any, tensor2: Any, dim: int = -1) -> Any:
        """Concatenate two tensors along specified dimension."""
        if tensor1 is None:
            return tensor2
        if tensor2 is None:
            return tensor1

        arr1 = tensor1 if isinstance(tensor1, np.ndarray) else np.array(tensor1)
        arr2 = tensor2 if isinstance(tensor2, np.ndarray) else np.array(tensor2)

        result = np.concatenate([arr1, arr2], axis=dim)
        return result.tolist()

    def get_kv_cache_shape(self) -> Optional[Tuple[int, ...]]:
        """Get KV cache shape - not available via API."""
        return None

    def get_num_layers(self) -> int:
        """Get the number of layers - not available via API."""
        return 32  # Reasonable default

    def get_vocab(self) -> Dict[str, int]:
        """Get the model's vocabulary."""
        # Return cached vocabulary
        if self._token_cache:
            return {v: k for k, v in self._token_cache.items()}
        # Return minimal pseudo-vocabulary
        return {f"<token_{i}>": i for i in range(min(1000, self._vocab_size))}

    def append_to_input(self, input_ids: Any, new_token_id: int) -> Any:
        """Append a new token to input_ids."""
        if isinstance(input_ids, list):
            return input_ids + [new_token_id]
        elif isinstance(input_ids, np.ndarray):
            return np.append(input_ids, new_token_id).tolist()
        else:
            return [new_token_id]

    def get_device(self) -> str:
        """Get device type."""
        return "huggingface-api"
