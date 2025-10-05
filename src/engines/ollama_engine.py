import time
import json
from typing import List, Tuple, Optional, Dict, Any
import subprocess

try:
    import numpy as np
except ImportError:
    raise ImportError("'numpy' library not found. Install with `pip install numpy`")

from src.core.engine_interface import LLMEngine
from src.engines import sampling_utils


class OllamaEngine(LLMEngine):
    """Engine for running models via Ollama."""

    def __init__(self, model_name: str, engine_specific_config: Optional[Dict[str, Any]] = None):
        super().__init__(model_name=model_name, engine_specific_config=engine_specific_config)
        self.base_url = engine_specific_config.get("ollama_url", "http://localhost:11434") if engine_specific_config else "http://localhost:11434"
        self._vocab_cache = {}
        self._vocab_size = None

    def load(self):
        """Load/verify the Ollama model."""
        print(f"OllamaEngine: Checking availability of model '{self.model_name}'...")

        # Check if ollama is installed
        try:
            result = subprocess.run(['ollama', 'list'], capture_output=True, text=True, check=True)
            available_models = result.stdout

            # Check if our model is in the list
            if self.model_name not in available_models:
                print(f"\nAvailable Ollama models:")
                print(available_models)
                raise RuntimeError(f"Model '{self.model_name}' not found in Ollama. Run: ollama pull {self.model_name}")

            print(f"✓ Model '{self.model_name}' is available via Ollama")

            # Get model info to extract vocabulary size
            self._initialize_vocabulary()

        except FileNotFoundError:
            raise RuntimeError("Ollama not found. Install from https://ollama.ai")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to list Ollama models: {e}")

    def _initialize_vocabulary(self):
        """Initialize vocabulary information by making a test inference."""
        try:
            # Make a simple API call to get tokenization info
            result = subprocess.run(
                ['ollama', 'run', self.model_name, '--verbose', 'test'],
                capture_output=True,
                text=True,
                timeout=30
            )
            # Set a reasonable default vocab size
            self._vocab_size = 32000  # Common for many models
            print(f"OllamaEngine: Using vocabulary size {self._vocab_size}")
        except Exception as e:
            print(f"Warning: Could not determine vocabulary size: {e}")
            self._vocab_size = 32000

    def get_vocabulary_size(self) -> int:
        """Return the vocabulary size."""
        return self._vocab_size or 32000

    def encode(self, text: str, add_special_tokens: bool = True) -> Tuple[List[int], None]:
        """
        Encode text to token IDs.
        Note: Ollama doesn't expose tokenization directly, so we approximate.
        """
        # This is a limitation - Ollama doesn't expose tokenization
        # For game purposes, we'll create pseudo-tokens based on words
        tokens = text.split()
        token_ids = [hash(token) % self._vocab_size for token in tokens]
        return (token_ids, None)

    def decode(self, token_ids: Any, skip_special_tokens: bool = False) -> str:
        """
        Decode token IDs to text.
        Note: Limited functionality with Ollama's API.
        """
        # Reverse lookup from cache if available
        if isinstance(token_ids, (list, tuple)):
            tokens = [self._vocab_cache.get(tid, f"<token_{tid}>") for tid in token_ids]
            return " ".join(tokens)
        else:
            return self._vocab_cache.get(int(token_ids), f"<token_{token_ids}>")

    def predict_next(
        self,
        input_ids: List[int],
        attention_mask: Any,
        temperature: float,
        top_k: int,
        top_p: float,
        output_attentions: bool = False,
        output_hidden_states: bool = False
    ) -> Dict[str, Any]:
        """
        Predict next token using Ollama.
        Note: This is simplified as Ollama doesn't expose full logits.
        """
        st = time.time()

        # Decode current tokens to text
        current_text = self.decode(input_ids)

        # Call Ollama API to generate next tokens
        try:
            import requests
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": current_text,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "top_k": top_k,
                        "top_p": top_p,
                        "num_predict": 1
                    }
                },
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            generated_text = result.get("response", "")

            # Extract the next token (approximate)
            next_token_text = generated_text.strip().split()[0] if generated_text.strip() else ""
            next_token_id = hash(next_token_text) % self._vocab_size

            # Cache the token
            self._vocab_cache[next_token_id] = next_token_text

            # Create synthetic logits (since Ollama doesn't expose them)
            logits_raw = np.full(self._vocab_size, -10.0, dtype=np.float32)
            logits_raw[next_token_id] = 1.0  # High score for predicted token

            # Add some noise to other tokens
            num_alternatives = min(top_k - 1, 10)
            for i in range(num_alternatives):
                alt_id = (next_token_id + i + 1) % self._vocab_size
                logits_raw[alt_id] = -1.0 - (i * 0.5)

            probs_raw = sampling_utils.softmax(logits_raw)

            # Get top tokens
            top_indices = np.argsort(logits_raw)[-top_k:][::-1]
            top_tokens = [self.get_token_text(idx) for idx in top_indices]
            top_probs = probs_raw[top_indices].tolist()

            return {
                "next_token_id": next_token_id,
                "logits_raw": logits_raw,
                "logits_processed": logits_raw,
                "probabilities_raw": probs_raw,
                "probabilities_temp": probs_raw,
                "probabilities_top_k": probs_raw,
                "probabilities_processed": probs_raw,
                "top_tokens_processed": top_tokens,
                "top_probs_processed": top_probs,
                "top_token_ids_processed": top_indices.tolist(),
                "attention": None,
                "hidden_states": None,
                "forward_time": time.time() - st
            }

        except ImportError:
            raise RuntimeError("'requests' library required for Ollama. Install with: pip install requests")
        except Exception as e:
            raise RuntimeError(f"Ollama API call failed: {e}")

    def get_token_text(self, token_id: int) -> str:
        """Get the text representation of a token ID."""
        return self._vocab_cache.get(token_id, f"<token_{token_id}>")

    def reset_kv_cache(self):
        """Reset any cached state."""
        # Ollama manages its own cache
        pass

    def get_config_summary(self) -> Dict[str, Any]:
        """Return configuration summary."""
        return {
            "Engine": "Ollama",
            "Model": self.model_name,
            "Base URL": self.base_url,
            "Vocab Size": self._vocab_size
        }
