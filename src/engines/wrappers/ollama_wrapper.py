import time
import json
import os
from typing import List, Tuple, Optional, Dict, Any
import subprocess
import gguf
from transformers import PreTrainedTokenizer

class GGUFTokenizer(PreTrainedTokenizer):
    def __init__(self, vocab_data, **kwargs):
        super().__init__(**kwargs)
        # Handle different vocab data formats
        if isinstance(vocab_data, (list, tuple)):
            self._vocab = list(vocab_data)
        elif hasattr(vocab_data, 'tolist'):
            # numpy array
            self._vocab = vocab_data.tolist()
        else:
            # Try to convert to list
            try:
                self._vocab = list(vocab_data)
            except:
                raise ValueError(f"Cannot convert vocab_data of type {type(vocab_data)} to list")

        # Decode bytes to strings if needed
        self._vocab = [
            token.decode('utf-8') if isinstance(token, bytes) else str(token)
            for token in self._vocab
        ]

        self.id_to_token = {i: token for i, token in enumerate(self._vocab)}

    @property
    def vocab_size(self):
        return len(self._vocab)

    def _tokenize(self, text):
        # This is a very simple tokenizer, it splits by space.
        # A more sophisticated implementation would use the sentencepiece model from the GGUF file.
        return text.split(' ')

    def _convert_token_to_id(self, token):
        return self._vocab.index(token) if token in self._vocab else self.unk_token_id

    def _convert_id_to_token(self, index):
        return self.id_to_token.get(index, self.unk_token)

    def get_vocab(self):
        return {token: i for i, token in enumerate(self._vocab)}

    def save_vocabulary(self, save_directory, filename_prefix=None):
        # This is required by the PreTrainedTokenizer interface
        return (os.path.join(save_directory, 'vocab.txt'),)


class PseudoTokenizer:
    """Minimal fallback tokenizer for when GGUF parsing fails."""
    def __init__(self, vocab_size=32000, model_name="ollama-pseudo"):
        self._vocab_size = vocab_size
        self._token_cache = {}
        self.name_or_path = model_name
        self.model_max_length = 2048
        self.eos_token_id = 2
        self.bos_token_id = 1
        self.pad_token_id = 0
        self.unk_token_id = 0

    @property
    def vocab_size(self):
        return self._vocab_size

    def encode(self, text, add_special_tokens=True):
        """Simple hash-based encoding."""
        tokens = text.split()
        return [hash(token) % self._vocab_size for token in tokens]

    def decode(self, token_ids, skip_special_tokens=False):
        """Decode from cached tokens."""
        if isinstance(token_ids, (list, tuple)):
            return " ".join(self._token_cache.get(tid, f"<{tid}>") for tid in token_ids)
        return self._token_cache.get(token_ids, f"<{token_ids}>")

    def get_vocab(self):
        """Return pseudo-vocabulary."""
        # Return a dictionary with at least some common tokens
        vocab = {f"<token_{i}>": i for i in range(min(1000, self._vocab_size))}
        vocab.update(self._token_cache)
        return vocab

    def cache_token(self, token_id, text):
        """Cache a token for later decoding."""
        self._token_cache[token_id] = text

try:
    import numpy as np
except ImportError:
    raise ImportError("'numpy' library not found. Install with `pip install numpy`")

from src.core.engine_interface import LLMEngine
from src.core import ollama_utils
from src.engines import sampling_utils


class OllamaEngine(LLMEngine):
    """Engine for running models via Ollama."""

    def __init__(self, model_name: str, engine_specific_config: Optional[Dict[str, Any]] = None):
        super().__init__(model_name=model_name, engine_specific_config=engine_specific_config)
        # Try to auto-detect if no URL specified
        config_url = engine_specific_config.get("ollama_url") if engine_specific_config else None
        if config_url:
            self.base_url = config_url
        else:
            # Auto-detect Ollama server
            self.base_url = ollama_utils.detect_ollama_server()
        self._vocab_cache = {}
        self._vocab_size = None
        self._model_info = None

    def load(self):
        """Load/verify the Ollama model and load its tokenizer from the GGUF file."""
        print(f"OllamaEngine: Checking availability of model '{self.model_name}'...")

        if not ollama_utils.is_ollama_installed():
            raise RuntimeError("Ollama CLI not found in PATH. Install from: https://ollama.ai")

        if self.base_url is None:
            self.base_url = ollama_utils.detect_ollama_server()
            if self.base_url is None:
                raise RuntimeError("Ollama server not found. Is it running? Start with: ollama serve")
            print(f"✓ Detected Ollama server at {self.base_url}")

        is_available, message = ollama_utils.check_model_availability(self.model_name, self.base_url)

        if not is_available:
            print(f"\n{message}")
            print(f"Model '{self.model_name}' not found locally. Attempting to download...")
            try:
                subprocess.run(['ollama', 'pull', self.model_name], check=True, text=True)
                print(f"\n✓ Model '{self.model_name}' downloaded successfully.")
            except subprocess.CalledProcessError as e:
                raise RuntimeError(f"Failed to download model '{self.model_name}'. Error: {e}")
            except FileNotFoundError:
                raise RuntimeError("'ollama' command not found. Please make sure Ollama is installed and in your PATH.")

        print("✓ Model is available.")

        # Get GGUF file path and load tokenizer
        try:
            model_info = ollama_utils.get_model_info(self.model_name, self.base_url)
            modelfile_content = model_info.get('modelfile', '')
            from_line = next((line for line in modelfile_content.split('\n') if line.startswith('FROM ')), None)
            if not from_line:
                raise RuntimeError("Could not find 'FROM' line in modelfile to locate GGUF file.")
            
            gguf_path = from_line.split(' ', 1)[1]
            if not os.path.exists(gguf_path):
                raise RuntimeError(f"GGUF file not found at path: {gguf_path}")

            reader = gguf.GGUFReader(gguf_path, 'r')

            # Find the vocabulary using the updated GGUF API
            field = reader.get_field('tokenizer.ggml.tokens')

            if field and hasattr(field, 'data'):
                # New API: data attribute contains the vocabulary
                vocab = field.data
                self.tokenizer = GGUFTokenizer(vocab)
                self._vocab_size = self.tokenizer.vocab_size
                print(f"✓ Tokenizer loaded from GGUF file. Vocab size: {self._vocab_size}")
            elif field and hasattr(field, 'parts'):
                # Old API fallback: try parts
                vocab = field.parts[-1] if field.parts else None
                if vocab:
                    self.tokenizer = GGUFTokenizer(vocab)
                    self._vocab_size = self.tokenizer.vocab_size
                    print(f"✓ Tokenizer loaded from GGUF file. Vocab size: {self._vocab_size}")
                else:
                    raise RuntimeError("Could not extract vocabulary from GGUF field.")
            else:
                raise RuntimeError("Could not find vocabulary in GGUF file.")

        except Exception as e:
            print(f"Warning: Could not load tokenizer from GGUF file: {e}")
            # Fallback to pseudo-tokenization if GGUF parsing fails
            self._initialize_vocabulary()

    def _initialize_vocabulary(self):
        """Fallback for pseudo-tokenization if GGUF parsing fails."""
        print("Warning: GGUF parsing failed. Falling back to pseudo-tokenization.")
        self._vocab_size = 32000
        self.tokenizer = PseudoTokenizer(self._vocab_size)

    def get_vocabulary_size(self) -> int:
        """Return the vocabulary size."""
        if self.tokenizer:
            return self.tokenizer.vocab_size
        return self._vocab_size or 32000

    def get_token_text(self, token_id: int) -> str:
        """Get text representation of a token ID."""
        if self.tokenizer:
            return self.tokenizer.decode([token_id])
        return self._vocab_cache.get(token_id, f"<token_{token_id}>")

    def encode(self, text: str, add_special_tokens: bool = True) -> Tuple[List[List[int]], None]:
        """Encode text to token IDs."""
        if self.tokenizer:
            return self.tokenizer.encode(text, add_special_tokens=add_special_tokens), None
        # Fallback to pseudo-tokenization
        tokens = text.split()
        token_ids = [hash(token) % self._vocab_size for token in tokens]
        return ([token_ids], None)

    def decode(self, token_ids: Any, skip_special_tokens: bool = False) -> str:
        """Decode token IDs to text."""
        if self.tokenizer:
            return self.tokenizer.decode(token_ids, skip_special_tokens=skip_special_tokens)
        
        # Fallback to pseudo-tokenization
        if isinstance(token_ids, list) and len(token_ids) > 0 and isinstance(token_ids[0], list):
            token_ids = token_ids[0]

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

            # Extract the next token from generated text
            next_token_text = generated_text.strip().split()[0] if generated_text.strip() else ""

            if not next_token_text:
                # Fallback to a default token if generation is empty
                next_token_text = " "

            if self.tokenizer:
                encoded = self.tokenizer.encode(next_token_text)
                next_token_id = encoded[0] if encoded else hash(next_token_text) % self._vocab_size
            else:
                next_token_id = hash(next_token_text) % self._vocab_size

            # Cache the token
            self._vocab_cache[next_token_id] = next_token_text
            if isinstance(self.tokenizer, PseudoTokenizer):
                self.tokenizer.cache_token(next_token_id, next_token_text)

            # Create synthetic logits (since Ollama doesn't expose them)
            vocab_size = self.get_vocabulary_size()
            logits_raw = np.full(vocab_size, -10.0, dtype=np.float32)
            logits_raw[next_token_id] = 1.0  # High score for predicted token

            # Add some noise to other tokens
            num_alternatives = min(top_k - 1, 10)
            for i in range(num_alternatives):
                alt_id = (next_token_id + i + 1) % vocab_size
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
                "probabilities": probs_raw,
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

    def _decode_token_raw(self, token_id: int) -> str:
        """Decode a single token ID using Ollama vocabulary cache."""
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

    def get_attention_for_visualization(self, attention_output: Any, input_ids_for_viz: Any) -> Optional[Tuple[List[str], List[float]]]:
        """Get attention weights for visualization."""
        # Ollama doesn't expose attention weights
        return None

    def get_probabilities_at_step(self, logits_or_probs: Any, step_name: str, k: int) -> Tuple[List[str], List[float], List[int]]:
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
            raise TypeError(f"OllamaEngine: Cannot convert {type(tensor)} to numpy array")

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

        # Convert to numpy if needed
        arr1 = tensor1 if isinstance(tensor1, np.ndarray) else np.array(tensor1)
        arr2 = tensor2 if isinstance(tensor2, np.ndarray) else np.array(tensor2)

        # Concatenate
        result = np.concatenate([arr1, arr2], axis=dim)
        return result.tolist()

    def get_kv_cache_shape(self) -> Optional[Tuple[int, ...]]:
        """Get KV cache shape if available."""
        # Ollama manages KV cache internally
        return None

    def get_num_layers(self) -> int:
        """Get the number of layers in the model."""
        # Ollama doesn't expose this, return reasonable default
        return 32

    def get_vocab(self) -> Dict[str, int]:
        """Get the model's vocabulary."""
        if self.tokenizer and hasattr(self.tokenizer, 'get_vocab'):
            return self.tokenizer.get_vocab()
        # Return the cached vocabulary or a pseudo-vocab for fallback
        if self._vocab_cache:
            return {v: k for k, v in self._vocab_cache.items()}
        # Return a minimal pseudo-vocabulary for compatibility
        return {f"<token_{i}>": i for i in range(min(1000, self._vocab_size or 32000))}

    # KV cache bridging: Using default "not supported" implementations from base class

    def append_to_input(self, input_ids: Any, new_token_id: int) -> Any:
        """Append a new token to input_ids tensor."""
        if isinstance(input_ids, list):
            return input_ids + [new_token_id]
        elif isinstance(input_ids, np.ndarray):
            return np.append(input_ids, new_token_id).tolist()
        else:
            return [new_token_id]

    def get_device(self) -> str:
        """Get device type (cpu, cuda, mps, etc)."""
        # Ollama manages its own device selection
        return "ollama-managed"
