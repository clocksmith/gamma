"""
OpenAI API Wrapper

Speed-optimized wrapper for OpenAI's API (GPT-3.5, GPT-4, etc.).
Provides fast inference without local model loading, but NO real logits access.

Limitations:
- Synthetic logits only (not real pre-softmax values)
- No attention weights
- No hidden states
- Not compatible with Mind Meld mode

Ideal for: Fast text generation with OpenAI models without needing probability distributions
"""

import time
import os
from typing import List, Tuple, Optional, Dict, Any

try:
    import numpy as np
    import requests
except ImportError:
    raise ImportError("OpenAI API requires 'numpy' and 'requests'. Install with: pip install numpy requests")

from src.core.engine_interface import LLMEngine
from src.core.types import PredictionResult
from src.engines import sampling_utils


class OpenAIEngine(LLMEngine):
    """Engine for OpenAI API (GPT-3.5, GPT-4, etc.)."""

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
        Initialize OpenAI API engine.

        Args:
            model_name: OpenAI model name (e.g., 'gpt-4', 'gpt-3.5-turbo', 'gpt-4o')
            engine_specific_config: Optional configuration dict with:
                - openai_api_key: OpenAI API key (or set OPENAI_API_KEY env var)
                - openai_org_id: OpenAI organization ID (optional)
                - api_base: Custom API endpoint (for Azure OpenAI, etc.)
        """
        super().__init__(model_name=model_name, engine_specific_config=engine_specific_config)

        # Get API key from config or environment
        self.api_key = (
            self.engine_config.get("openai_api_key") or
            os.environ.get("OPENAI_API_KEY")
        )

        if not self.api_key:
            raise ValueError(
                "OpenAI API requires an API key. "
                "Set via --openai-api-key argument or OPENAI_API_KEY environment variable. "
                "Get your API key at: https://platform.openai.com/api-keys"
            )

        # Optional organization ID
        self.org_id = self.engine_config.get("openai_org_id") or os.environ.get("OPENAI_ORG_ID")

        # API endpoint (default to OpenAI, but can be customized for Azure, etc.)
        self.api_base = self.engine_config.get("api_base", "https://api.openai.com/v1")

        # Request headers
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        if self.org_id:
            self.headers["OpenAI-Organization"] = self.org_id

        # Vocab size estimate (GPT models use ~50k tokens)
        self._vocab_size = 50257  # GPT-2/3 vocab size
        self._token_cache = {}

        # Message history for chat
        self._message_history = []

    def load(self):
        """Verify API connection and model availability."""
        print(f"OpenAIEngine: Checking API access for '{self.model_name}'...")

        # Test API connection
        try:
            test_response = requests.post(
                f"{self.api_base}/chat/completions",
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
                print(f"✓ Successfully connected to OpenAI API")
                print(f"  Model: {self.model_name}")
                print(f"  Endpoint: {self.api_base}")
            elif test_response.status_code == 401:
                raise RuntimeError(
                    "Authentication failed. Invalid OpenAI API key. "
                    "Get your API key at: https://platform.openai.com/api-keys"
                )
            elif test_response.status_code == 404:
                raise RuntimeError(
                    f"Model '{self.model_name}' not found. "
                    f"Check available models at: https://platform.openai.com/docs/models"
                )
            elif test_response.status_code == 429:
                print("Warning: Rate limit or quota exceeded (HTTP 429)")
                print("Continuing anyway - API may work with different parameters")
            else:
                print(f"Warning: API returned status {test_response.status_code}: {test_response.text}")
                print("Continuing anyway - API may still work for generation")

        except requests.exceptions.Timeout:
            raise RuntimeError("OpenAI API request timed out. Check your network connection.")
        except requests.exceptions.ConnectionError:
            raise RuntimeError("Cannot connect to OpenAI API. Check your network connection.")
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
        Predict next token using OpenAI API.

        Note: This generates synthetic logits as the API only returns text.
        """
        st = time.time()

        # Decode current tokens to text
        current_text = self.decode(input_ids)

        # Build chat message
        messages = [{"role": "user", "content": current_text}]

        # Call OpenAI API
        try:
            payload = {
                "model": self.model_name,
                "messages": messages,
                "max_tokens": 1,  # Only generate next token
                "temperature": temperature,
                "top_p": top_p,
                "stream": False
            }

            response = requests.post(
                f"{self.api_base}/chat/completions",
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
                raise RuntimeError("OpenAI API rate limit exceeded. Check your usage limits and billing.")
            elif e.response.status_code == 503:
                raise RuntimeError("OpenAI API is currently unavailable. Try again later.")
            else:
                raise RuntimeError(f"OpenAI API error ({e.response.status_code}): {e.response.text}")
        except Exception as e:
            raise RuntimeError(f"OpenAI API call failed: {e}")

    def get_vocabulary_size(self) -> int:
        """Return vocabulary size."""
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
            "Engine": "OpenAI API",
            "Model": self.model_name,
            "API Endpoint": self.api_base,
            "Organization": self.org_id or "Default",
            "API Key": f"{self.api_key[:8]}..." if self.api_key else "None"
        }

    def convert_to_numpy(self, tensor: Any) -> np.ndarray:
        """Convert engine-specific tensor to numpy array."""
        if isinstance(tensor, np.ndarray):
            return tensor
        elif isinstance(tensor, list):
            return np.array(tensor)
        else:
            raise TypeError(f"OpenAIEngine: Cannot convert {type(tensor)} to numpy array")

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

    def get_num_layers(self) -> int:
        """Get the number of layers - not available via API."""
        return 32  # Reasonable default

    def get_vocab(self) -> Dict[str, int]:
        """Get the model's vocabulary."""
        if self._token_cache:
            return {v: k for k, v in self._token_cache.items()}
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
        return "openai-api"
