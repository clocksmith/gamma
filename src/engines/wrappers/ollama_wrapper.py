import time
import json
import os
from typing import List, Tuple, Optional, Dict, Any, Union
import gguf

from src.core import config as cfg
try:
    import sentencepiece as spm
except ImportError:
    spm = None


def _ensure_quantization_support():
    """Patch gguf quantization enum to tolerate newer types we don't use directly."""
    try:
        from gguf import GGMLQuantizationType
        # Some Ollama models use legacy id 4 which older gguf packages don't map.
        if 4 not in GGMLQuantizationType._value2member_map_:
            # Treat it as Q4_1 (same as id 3) so reader can continue.
            GGMLQuantizationType._value2member_map_[4] = GGMLQuantizationType.Q4_1
    except Exception:
        pass

class GGUFTokenizer:
    """Lightweight tokenizer that reads vocabulary directly from GGUF metadata."""

    def __init__(self, vocab_data, special_token_ids: Optional[Dict[str, int]] = None):
        # Normalize vocab into a Python list of strings
        if isinstance(vocab_data, (list, tuple)):
            raw_vocab = list(vocab_data)
        elif hasattr(vocab_data, "tolist"):
            raw_vocab = vocab_data.tolist()
        else:
            try:
                raw_vocab = list(vocab_data)
            except Exception as exc:
                raise ValueError(f"Cannot convert vocab_data of type {type(vocab_data)} to list") from exc

        self._vocab: List[str] = [
            token.decode("utf-8", errors="replace") if isinstance(token, (bytes, bytearray)) else str(token)
            for token in raw_vocab
        ]
        self._token_to_id: Dict[str, int] = {token: idx for idx, token in enumerate(self._vocab)}
        self._special_token_ids = special_token_ids or {}

        # Resolve special token strings/ids with fallbacks
        self.pad_token_id = self._resolve_special_id("pad", default=0)
        self.unk_token_id = self._resolve_special_id("unk", default=self.pad_token_id)
        self.bos_token_id = self._resolve_special_id("bos", default=None)
        self.eos_token_id = self._resolve_special_id("eos", default=None)

        self.pad_token = self._token_by_id(self.pad_token_id) or "<pad>"
        self.unk_token = self._token_by_id(self.unk_token_id) or "<unk>"
        self.bos_token = self._token_by_id(self.bos_token_id) or "<s>"
        self.eos_token = self._token_by_id(self.eos_token_id) or "</s>"

        self.model_max_length = 2048

    def _resolve_special_id(self, key: str, default: Optional[int]) -> Optional[int]:
        if key in self._special_token_ids:
            value = self._special_token_ids[key]
            if isinstance(value, (list, tuple)):
                value = value[0]
            try:
                int_val = int(value)
            except (TypeError, ValueError):
                int_val = default
            return int_val
        return default

    def _token_by_id(self, index: Optional[int]) -> Optional[str]:
        if index is None:
            return None
        if 0 <= index < len(self._vocab):
            return self._vocab[index]
        return None

    @property
    def vocab_size(self) -> int:
        return len(self._vocab)

    def get_vocab(self) -> Dict[str, int]:
        return dict(self._token_to_id)

    # HuggingFace-compatible helpers -------------------------------------------------
    def convert_tokens_to_ids(self, tokens: Union[str, List[str]]) -> Union[int, List[int]]:
        if isinstance(tokens, str):
            return self._convert_token_to_id(tokens)
        return [self._convert_token_to_id(token) for token in tokens]

    def convert_ids_to_tokens(self, indices: Union[int, List[int]]) -> Union[str, List[str]]:
        if isinstance(indices, int):
            return self._convert_id_to_token(indices)
        return [self._convert_id_to_token(idx) for idx in indices]

    def encode(self, text: str, add_special_tokens: bool = True) -> List[int]:
        token_strings = self._tokenize(text)
        return [self._convert_token_to_id(token) for token in token_strings]

    def decode(self, token_ids: Union[int, List[int]], skip_special_tokens: bool = False) -> str:
        if isinstance(token_ids, int):
            token_ids = [token_ids]

        pieces: List[str] = []
        previous_was_space = False
        for idx in token_ids:
            token = self._convert_id_to_token(idx)
            if token is None:
                continue
            if skip_special_tokens and idx in {
                tid for tid in [self.pad_token_id, self.unk_token_id, self.bos_token_id, self.eos_token_id] if tid is not None
            }:
                continue

            if token in {"Ċ", "ĠĊ"}:
                pieces.append("\n")
                previous_was_space = True
                continue

            if token.startswith("▁"):
                text_fragment = token[1:]
                if pieces and not previous_was_space:
                    pieces.append(" ")
                pieces.append(text_fragment)
                previous_was_space = True
            elif token.startswith("Ġ"):
                text_fragment = token[1:]
                if pieces and not previous_was_space:
                    pieces.append(" ")
                pieces.append(text_fragment)
                previous_was_space = True
            else:
                pieces.append(token)
                previous_was_space = False

        return "".join(pieces)

    # Internal helpers ----------------------------------------------------------------
    def _tokenize(self, text: str) -> List[str]:
        if not text:
            return []

        # Simple heuristic tokenization: split on whitespace, then map using common SP conventions
        tokens: List[str] = []
        raw_parts = text.strip().split()

        for part in raw_parts:
            candidates: List[str] = [part]
            stripped = part.strip()
            if stripped and not stripped.startswith("▁"):
                candidates.insert(0, f"▁{stripped}")
                candidates.append(f" {stripped}")

            if stripped:
                for variant in (stripped.lower(), stripped.capitalize(), stripped.upper()):
                    if variant and variant not in candidates:
                        candidates.append(variant)

            resolved_token = None
            for candidate in candidates:
                if candidate in self._token_to_id:
                    resolved_token = candidate
                    break

            tokens.append(resolved_token if resolved_token is not None else (stripped or part))

        return tokens

    def _convert_token_to_id(self, token: str) -> int:
        if token in self._token_to_id:
            return self._token_to_id[token]

        stripped = token.strip()
        for candidate in (
            stripped,
            token,
            f"▁{stripped}" if stripped else token,
            stripped.lower(),
            stripped.capitalize(),
            stripped.upper(),
        ):
            if candidate in self._token_to_id:
                return self._token_to_id[candidate]

        return self.unk_token_id if self.unk_token_id is not None else 0

    def _convert_id_to_token(self, index: int) -> Optional[str]:
        return self._token_by_id(index)

    def save_vocabulary(self, save_directory: str, filename_prefix: Optional[str] = None):
        vocab_path = os.path.join(save_directory, f"{filename_prefix + '-' if filename_prefix else ''}vocab.txt")
        with open(vocab_path, "w", encoding="utf-8") as vocab_file:
            for token in self._vocab:
                vocab_file.write(f"{token}\n")
        return (vocab_path,)


class SentencePieceTokenizerWrapper:
    """Thin wrapper around a SentencePieceProcessor to match engine expectations."""

    def __init__(self, processor: "spm.SentencePieceProcessor", special_token_ids: Optional[Dict[str, int]] = None):
        self._sp = processor
        self._special_token_ids = special_token_ids or {}

        self.pad_token_id = self._special_token_ids.get("pad", getattr(self._sp, "pad_id", lambda: -1)())
        self.unk_token_id = self._special_token_ids.get("unk", self._sp.unk_id())
        self.bos_token_id = self._special_token_ids.get("bos", getattr(self._sp, "bos_id", lambda: -1)())
        self.eos_token_id = self._special_token_ids.get("eos", getattr(self._sp, "eos_id", lambda: -1)())

        self.pad_token = self.id_to_piece(self.pad_token_id) if self.pad_token_id >= 0 else "<pad>"
        self.unk_token = self.id_to_piece(self.unk_token_id) if self.unk_token_id >= 0 else "<unk>"
        self.bos_token = self.id_to_piece(self.bos_token_id) if self.bos_token_id >= 0 else "<s>"
        self.eos_token = self.id_to_piece(self.eos_token_id) if self.eos_token_id >= 0 else "</s>"

        # SentencePiece exposes this attribute
        self.model_max_length = getattr(self._sp, "model_proto", None) and 2048

    @property
    def vocab_size(self) -> int:
        return self._sp.get_piece_size()

    def id_to_piece(self, idx: int) -> str:
        return self._sp.id_to_piece(idx) if idx >= 0 else ""

    def piece_to_id(self, piece: str) -> int:
        return self._sp.piece_to_id(piece)

    def convert_ids_to_tokens(self, indices: Union[int, List[int]]) -> Union[str, List[str]]:
        if isinstance(indices, int):
            return self.id_to_piece(indices)
        return [self.id_to_piece(idx) for idx in indices]

    def convert_tokens_to_ids(self, tokens: Union[str, List[str]]) -> Union[int, List[int]]:
        if isinstance(tokens, str):
            return self.piece_to_id(tokens)
        return [self.piece_to_id(tok) for tok in tokens]

    def encode(self, text: str, add_special_tokens: bool = True) -> List[int]:
        ids = self._sp.encode(text, out_type=int)
        if add_special_tokens:
            if self.bos_token_id is not None and self.bos_token_id >= 0:
                ids = [self.bos_token_id] + ids
            if self.eos_token_id is not None and self.eos_token_id >= 0:
                ids = ids + [self.eos_token_id]
        return ids

    def decode(self, token_ids: Union[int, List[int]], skip_special_tokens: bool = False) -> str:
        if isinstance(token_ids, int):
            token_ids = [token_ids]
        if skip_special_tokens:
            specials = {
                tid
                for tid in [
                    self.pad_token_id,
                    self.unk_token_id,
                    self.bos_token_id,
                    self.eos_token_id,
                ]
                if tid is not None and tid >= 0
            }
            token_ids = [tid for tid in token_ids if tid not in specials]
        return self._sp.decode(token_ids)

    def get_vocab(self) -> Dict[str, int]:
        size = self.vocab_size
        return {self.id_to_piece(i): i for i in range(size)}


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


def _extract_field_data(field: Any) -> Optional[Any]:
    if field is None:
        return None
    if hasattr(field, "data"):
        return field.data
    if hasattr(field, "parts"):
        return field.parts
    return None


def _extract_vocab_list(field: Any) -> Optional[List[str]]:
    if field is None:
        return None

    if hasattr(field, "contents"):
        try:
            contents = field.contents()
            if isinstance(contents, list) and contents and isinstance(contents[0], str):
                return contents
        except Exception:
            pass

    data = _extract_field_data(field)
    if data is None:
        return None

    if isinstance(data, list):
        if data and isinstance(data[0], (bytes, bytearray)):
            return [bytes(entry).decode("utf-8", errors="replace") for entry in data]
        if data and hasattr(data[0], "__iter__") and not isinstance(data[0], str):
            tokens: List[str] = []
            for entry in data:
                try:
                    tokens.append(bytes(entry).decode("utf-8", errors="replace"))
                except Exception:
                    tokens.append(str(entry))
            return tokens
        return [str(entry) for entry in data]

    if hasattr(data, "__iter__") and not isinstance(data, (bytes, bytearray, str)):
        try:
            return [bytes(entry).decode("utf-8", errors="replace") for entry in data]
        except Exception:
            return [str(entry) for entry in data]

    if isinstance(data, (bytes, bytearray)):
        return [bytes(data).decode("utf-8", errors="replace")]

    return None


def _field_to_int(field: Any) -> Optional[int]:
    data = _extract_field_data(field)
    if data is None:
        return None
    try:
        if isinstance(data, (bytes, bytearray)):
            return int.from_bytes(data, "little")
        if isinstance(data, (list, tuple)):
            return int(data[0])
        import numpy as np  # Local import to avoid global dependency during type checks

        if isinstance(data, np.ndarray):
            return int(np.array(data).astype(np.int64).flat[0])
        return int(data)
    except Exception:
        return None


def _field_to_bytes(field: Any) -> Optional[bytes]:
    data = _extract_field_data(field)
    if data is None:
        return None
    if isinstance(data, bytes):
        return data
    if isinstance(data, bytearray):
        return bytes(data)
    if isinstance(data, (list, tuple)):
        try:
            return bytes(data)
        except Exception:
            pass
    try:
        import numpy as np

        if isinstance(data, np.ndarray):
            arr = np.asarray(data, dtype=np.uint8)
            return arr.tobytes()
    except Exception:
        pass
    return None

try:
    import numpy as np
except ImportError:
    raise ImportError("'numpy' library not found. Install with `pip install numpy`")

from src.core.engine_interface import LLMEngine
from src.core.types import PredictionResult
from src.core import ollama_utils
from src.engines import sampling_utils


class OllamaEngine(LLMEngine):
    """Engine for running models via Ollama."""

    _warned_missing_logprobs: bool = False

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
        OllamaEngine._warned_missing_logprobs = False

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
            raise RuntimeError(
                f"Model '{self.model_name}' not found locally. "
                f"Run: ollama pull {self.model_name}"
            )

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

            _ensure_quantization_support()
            reader = gguf.GGUFReader(gguf_path, 'r')

            special_token_ids: Dict[str, int] = {}
            for key in ["bos", "eos", "unk", "pad"]:
                field_name = f"tokenizer.ggml.{key}_token_id"
                value = _field_to_int(reader.get_field(field_name))
                if value is not None:
                    special_token_ids[key] = value

            # Try to locate an external SentencePiece model in the model directory
            if spm is not None:
                model_dir = os.path.dirname(gguf_path)
                candidate_names = [
                    "tokenizer.model",
                    "tokenizer_sp.model",
                    "tokenizer.spm",
                    "tokenizer.model.spm",
                ]
                candidate_paths = [os.path.join(model_dir, name) for name in candidate_names]
                # Also include any *.spm or *.model files in the directory
                for entry in os.listdir(model_dir):
                    if entry.endswith((".spm", ".model")):
                        candidate_paths.append(os.path.join(model_dir, entry))

                for path in candidate_paths:
                    if not os.path.isfile(path):
                        continue
                    try:
                        sp_processor = spm.SentencePieceProcessor()
                        sp_processor.Load(path)
                        self.tokenizer = SentencePieceTokenizerWrapper(sp_processor, special_token_ids)
                        self._vocab_size = self.tokenizer.vocab_size
                        print(f"✓ SentencePiece tokenizer loaded from {os.path.basename(path)}. Vocab size: {self._vocab_size}")
                        return
                    except Exception:
                        continue

            # Fallback: attempt to load serialized SentencePiece proto from GGUF
            tokenizer_model_bytes = _field_to_bytes(reader.get_field('tokenizer.ggml.model'))
            if tokenizer_model_bytes and spm is not None:
                try:
                    sp_processor = spm.SentencePieceProcessor()
                    sp_processor.LoadFromSerializedProto(tokenizer_model_bytes)
                    self.tokenizer = SentencePieceTokenizerWrapper(sp_processor, special_token_ids)
                    self._vocab_size = self.tokenizer.vocab_size
                    print(f"✓ SentencePiece tokenizer loaded from GGUF. Vocab size: {self._vocab_size}")
                    return
                except Exception as exc:
                    print(f"Warning: Failed to initialize SentencePiece tokenizer: {exc}")
            elif tokenizer_model_bytes and spm is None:
                print("Warning: sentencepiece library not installed; install with `pip install sentencepiece` for accurate token decoding.")

            # Final fallback to raw GGUF tokens if SentencePiece unavailable
            field = reader.get_field('tokenizer.ggml.tokens')
            vocab = _extract_vocab_list(field)
            if not vocab:
                raise RuntimeError("Could not find vocabulary in GGUF file.")

            self.tokenizer = GGUFTokenizer(vocab, special_token_ids=special_token_ids)
            self._vocab_size = self.tokenizer.vocab_size
            print(f"✓ Tokenizer loaded from GGUF tokens. Vocab size: {self._vocab_size}")

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
    ) -> PredictionResult:
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
            payload = {
                "model": self.model_name,
                "prompt": current_text,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "top_k": top_k,
                    "top_p": top_p,
                    "num_predict": 1,
                    "logprobs": max(top_k, cfg.DEFAULT_NUM_CHOICES)
                }
            }

            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            result = response.json()
            generated_text = result.get("response", "")

            logprob_info = result.get("logprobs") or {}
            token_candidates = []
            next_token_text = ""
            next_token_id = None

            if logprob_info:
                tokens_meta = logprob_info.get("tokens") or []
                # Look for the first generated token meta with top_logprobs
                for token_meta in tokens_meta:
                    candidate_token = token_meta.get("token")
                    top_meta = token_meta.get("top_logprobs") or []
                    if candidate_token:
                        next_token_text = candidate_token
                        token_candidates = top_meta if isinstance(top_meta, list) else []
                        break

            if not next_token_text:
                # Fallback to the raw generated text if logprobs not present
                next_token_text = generated_text.strip().split()[0] if generated_text.strip() else ""

            if not next_token_text:
                next_token_text = " "

            # Convert token to id
            if self.tokenizer:
                try:
                    encoded = self.tokenizer.convert_tokens_to_ids(next_token_text)
                    if isinstance(encoded, list):
                        encoded = encoded[0] if encoded else None
                    next_token_id = encoded if isinstance(encoded, int) else None
                except Exception:
                    next_token_id = None

            if next_token_id is None:
                if self.tokenizer:
                    encoded = self.tokenizer.encode(next_token_text, add_special_tokens=False)
                    next_token_id = encoded[0] if encoded else hash(next_token_text) % self.get_vocabulary_size()
                else:
                    next_token_id = hash(next_token_text) % self.get_vocabulary_size()

            # Cache the token for fallback decoding
            if self.tokenizer and hasattr(self.tokenizer, "cache_token"):
                self.tokenizer.cache_token(next_token_id, next_token_text)
            else:
                self._vocab_cache[next_token_id] = next_token_text

            # Build logits/probabilities either from logprobs or fallback synthetic data
            vocab_size = self.get_vocabulary_size()
            if token_candidates:
                logits_raw = np.full(vocab_size, -np.inf, dtype=np.float32)
                probs_raw = np.zeros(vocab_size, dtype=np.float32)

                def _candidate_to_id(token_str: str) -> int:
                    if not self.tokenizer:
                        return hash(token_str) % vocab_size
                    try:
                        cid = self.tokenizer.convert_tokens_to_ids(token_str)
                        if isinstance(cid, list):
                            cid = cid[0] if cid else None
                        if isinstance(cid, int) and cid >= 0:
                            return cid
                    except Exception:
                        pass
                    enc = self.tokenizer.encode(token_str, add_special_tokens=False) if self.tokenizer else []
                    return enc[0] if enc else hash(token_str) % vocab_size

                # Always include the predicted token
                logits_raw[next_token_id] = 0.0
                probs_raw[next_token_id] = 1.0

                top_tokens = []
                top_probs = []

                for candidate in token_candidates:
                    token_str = candidate.get("token")
                    logprob_val = candidate.get("logprob")
                    if token_str is None or logprob_val is None:
                        continue
                    tok_id = _candidate_to_id(token_str)
                    prob = float(np.exp(logprob_val))
                    probs_raw[tok_id] = prob
                    logits_raw[tok_id] = float(logprob_val)
                    top_tokens.append(token_str)
                    top_probs.append(prob)

                if top_tokens:
                    # Normalize probs to sum to 1 over included tokens
                    total_prob = float(np.sum(probs_raw[probs_raw > 0]))
                    if total_prob > 0:
                        probs_raw = probs_raw / total_prob
                    top_indices = [self.tokenizer.convert_tokens_to_ids(tok) if self.tokenizer else hash(tok) % vocab_size for tok in top_tokens]
                else:
                    # Fallback to synthetic if no candidate data
                    token_candidates = []

            if not token_candidates:
                if not OllamaEngine._warned_missing_logprobs:
                    print(
                        f"{cfg.COLOR_YELLOW}Notice: Ollama did not return logprobs for '{self.model_name}'. "
                        "Probability grid will use a synthetic fallback. Adjust settings or switch engines for more detailed statistics."
                        f"{cfg.COLOR_RESET}"
                    )
                    OllamaEngine._warned_missing_logprobs = True

                logits_raw = np.full(vocab_size, -10.0, dtype=np.float32)
                logits_raw[next_token_id] = 1.0
                probs_raw = sampling_utils.softmax(logits_raw)
                top_indices = np.argsort(logits_raw)[-top_k:][::-1]
                top_tokens = [self.get_token_text(idx) for idx in top_indices]
                top_probs = probs_raw[top_indices].tolist()
            else:
                # Align top tokens/probs from candidate list, ensure highest probability first
                if not top_tokens:
                    # Build from probs_raw array if not already filled
                    top_indices = np.argsort(probs_raw)[-top_k:][::-1]
                    top_tokens = [self.get_token_text(idx) for idx in top_indices]
                    top_probs = probs_raw[top_indices].tolist()
                else:
                    # Ensure predicted token appears first
                    if next_token_text not in top_tokens:
                        top_tokens.insert(0, next_token_text)
                        top_probs.insert(0, float(probs_raw[next_token_id]))
                    top_indices = [self.tokenizer.convert_tokens_to_ids(tok) if self.tokenizer else hash(tok) % vocab_size for tok in top_tokens]

            top_indices_array = np.array(top_indices, dtype=int)

            return PredictionResult.from_dict({
                "next_token_id": next_token_id,
                "logits_raw": logits_raw,
                "logits_processed": logits_raw,
                "logits_after_temperature": logits_raw,
                "logits_after_top_k": logits_raw,
                "logits_after_top_p": logits_raw,
                "probabilities": probs_raw,
                "probabilities_raw": probs_raw,
                "probabilities_temp": probs_raw,
                "probabilities_top_k": probs_raw,
                "probabilities_processed": probs_raw,
                "top_tokens_processed": top_tokens,
                "top_probs_processed": top_probs,
                "top_token_ids_processed": top_indices_array.tolist(),
                "attention": None,
                "hidden_states": None,
                "forward_time": time.time() - st
            })

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

    def convert_to_numpy(self, tensor: Any) -> np.ndarray:
        """Convert engine-specific tensor to numpy array."""
        if isinstance(tensor, np.ndarray):
            return tensor
        if isinstance(tensor, list):
            arr = np.array(tensor)
            if arr.ndim > 1:
                arr = arr.reshape(-1)
            return arr
        raise TypeError(f"OllamaEngine: Cannot convert {type(tensor)} to numpy array")

    def convert_from_numpy(self, array: np.ndarray) -> Any:
        """Convert numpy array to engine-specific tensor."""
        if isinstance(array, np.ndarray):
            flat = array.reshape(-1).tolist()
            return flat
        return array

    def concatenate_tensors(self, tensor1: Any, tensor2: Any, dim: int = -1) -> Any:
        """Concatenate two tensors along specified dimension."""
        if tensor1 is None:
            return tensor2
        if tensor2 is None:
            return tensor1

        arr1 = self.convert_to_numpy(tensor1)
        arr2 = self.convert_to_numpy(tensor2)
        # Ensure 1D
        arr1 = arr1.reshape(-1)
        arr2 = arr2.reshape(-1)
        result = np.concatenate([arr1, arr2])
        return result.tolist()

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
