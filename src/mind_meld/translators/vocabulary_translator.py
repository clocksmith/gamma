"""
Vocabulary translation and alignment strategies for Mind Meld.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

import numpy as np

from src.engines.sampling_utils import TRANSLATION_LOGIT_FLOOR

if TYPE_CHECKING:
    from transformers import PreTrainedTokenizerBase

logger = logging.getLogger(__name__)

_SPECIAL_TOKEN_ROLES: Tuple[str, ...] = (
    "bos",
    "eos",
    "unk",
    "pad",
    "sep",
    "cls",
    "mask",
)


@dataclass(frozen=True)
class TokenizerSpec:
    """Validated snapshot of a tokenizer's vocabulary and special-token semantics."""

    name: str
    vocab: Dict[str, int]
    id_to_token: Dict[int, str]
    vocab_size: int
    special_roles: Tuple[Tuple[str, Optional[str], Optional[int]], ...]
    additional_special_tokens: Tuple[str, ...]
    chat_template: Optional[str]
    has_codec: bool


@dataclass(frozen=True)
class TokenizerPairSpec:
    """Precomputed compatibility and vocabulary metadata for a (source, target) pair."""

    source: TokenizerSpec
    target: TokenizerSpec
    equal_vocab_mapping: bool
    equal_special_semantics: bool
    can_passthrough: bool


class VocabularyTranslator(ABC):
    """Abstract base class for translating logits between different vocabularies.

    Provides shared utility methods for tokenizer validation, pair-compatibility
    memoization, caching, flattening, and normalization across translator implementations.
    """

    # Default logit floor value (avoids -inf which causes softmax issues)
    # Imported from sampling_utils for consistency
    DEFAULT_LOGIT_FLOOR = TRANSLATION_LOGIT_FLOOR

    # Minimum mapped tokens before rejecting a non-trivial cross-vocabulary mapping
    MIN_MAPPED_TOKENS = 10

    # Whether this translator requires callable encode()/decode() on tokenizers
    REQUIRES_CODEC = False

    def __init__(
        self,
        use_cache: bool = True,
        verbose: bool = False,
        source_tokenizer: Optional['PreTrainedTokenizerBase'] = None,
        target_tokenizer: Optional['PreTrainedTokenizerBase'] = None,
        min_mapped_tokens: Optional[int] = None,
    ):
        """Initialize base translator and optionally pre-validate a tokenizer pair once."""
        self._cache: Dict[str, Any] = {}
        self._tokenizer_specs: Dict[int, Tuple[Any, TokenizerSpec]] = {}
        self._pair_specs: Dict[Tuple[int, int], Tuple[Any, Any, TokenizerPairSpec]] = {}
        self.use_cache = use_cache
        self.verbose = verbose
        self._explicit_min_mapped_tokens = min_mapped_tokens
        if min_mapped_tokens is not None:
            if isinstance(min_mapped_tokens, bool) or not isinstance(min_mapped_tokens, int) or min_mapped_tokens < 1:
                raise ValueError("min_mapped_tokens must be a positive integer")
            self.min_mapped_tokens = min_mapped_tokens
        else:
            self.min_mapped_tokens = self.MIN_MAPPED_TOKENS

        self._bound_source_tokenizer: Optional['PreTrainedTokenizerBase'] = None
        self._bound_target_tokenizer: Optional['PreTrainedTokenizerBase'] = None
        self._bound_pair_spec: Optional[TokenizerPairSpec] = None

        if (source_tokenizer is None) != (target_tokenizer is None):
            raise ValueError("Provide both source_tokenizer and target_tokenizer or neither")

        if source_tokenizer is not None and target_tokenizer is not None:
            self._bound_source_tokenizer = source_tokenizer
            self._bound_target_tokenizer = target_tokenizer
            self._bound_pair_spec = self._resolve_pair_spec(source_tokenizer, target_tokenizer)
            if not self._bound_pair_spec.can_passthrough:
                self._prebuild_pair(source_tokenizer, target_tokenizer, self._bound_pair_spec)

    def _prebuild_pair(
        self,
        source_tokenizer: 'PreTrainedTokenizerBase',
        target_tokenizer: 'PreTrainedTokenizerBase',
        pair_spec: TokenizerPairSpec,
    ) -> None:
        """Hook for subclasses to precompute alignment maps at construction time."""
        return None

    @staticmethod
    def _inspect_tokenizer(tokenizer: Any, role: str, require_codec: bool = False) -> TokenizerSpec:
        """Validate tokenizer introspection once and extract vocabulary + special-token semantics."""
        if tokenizer is None:
            raise ValueError(f"Unsupported {role} tokenizer introspection: tokenizer is None")

        get_vocab = getattr(tokenizer, "get_vocab", None)
        if not callable(get_vocab):
            raise ValueError(f"Unsupported {role} tokenizer introspection: missing callable get_vocab()")

        try:
            raw_vocab = get_vocab()
        except Exception as exc:
            raise ValueError(f"Unsupported {role} tokenizer introspection: get_vocab() failed: {exc}") from exc

        if not isinstance(raw_vocab, dict):
            raise ValueError(f"Unsupported {role} tokenizer introspection: get_vocab() must return a dict")

        vocab: Dict[str, int] = {}
        id_to_token: Dict[int, str] = {}
        for token_str, token_id in raw_vocab.items():
            if not isinstance(token_str, str):
                raise ValueError(f"Unsupported {role} tokenizer introspection: token key {token_str!r} is not a str")
            if isinstance(token_id, bool) or not isinstance(token_id, (int, np.integer)):
                raise ValueError(
                    f"Unsupported {role} tokenizer introspection: token '{token_str}' has non-integer ID {token_id!r}"
                )
            tid = int(token_id)
            if tid < 0:
                raise ValueError(
                    f"Unsupported {role} tokenizer introspection: token '{token_str}' has negative ID {tid}"
                )
            if tid in id_to_token and id_to_token[tid] != token_str:
                raise ValueError(
                    f"Unsupported {role} tokenizer introspection: duplicate token ID {tid} for "
                    f"'{id_to_token[tid]}' and '{token_str}'"
                )
            vocab[token_str] = tid
            id_to_token[tid] = token_str

        vocab_size = len(vocab)
        if vocab_size > 0:
            max_id = max(id_to_token.keys())
            if max_id >= vocab_size:
                raise ValueError(
                    f"Unsupported {role} tokenizer introspection: non-contiguous token ID {max_id} "
                    f"for vocabulary size {vocab_size}"
                )

        has_decode = callable(getattr(tokenizer, "decode", None))
        has_encode = callable(getattr(tokenizer, "encode", None))
        has_codec = has_decode and has_encode
        if require_codec and not has_codec:
            raise ValueError(
                f"Unsupported {role} tokenizer introspection: callable encode() and decode() are required"
            )

        special_roles: List[Tuple[str, Optional[str], Optional[int]]] = []
        for role_name in _SPECIAL_TOKEN_ROLES:
            tok_attr = getattr(tokenizer, f"{role_name}_token", None)
            id_attr = getattr(tokenizer, f"{role_name}_token_id", None)

            if tok_attr is not None and not isinstance(tok_attr, str):
                raise ValueError(
                    f"Unsupported {role} tokenizer introspection: {role_name}_token must be a str or None"
                )
            if id_attr is not None:
                if isinstance(id_attr, bool) or not isinstance(id_attr, (int, np.integer)):
                    raise ValueError(
                        f"Unsupported {role} tokenizer introspection: {role_name}_token_id must be an int or None"
                    )
                id_attr = int(id_attr)
                if vocab_size == 0 or not (0 <= id_attr < vocab_size):
                    raise ValueError(
                        f"Invalid {role} special token: {role_name}_token_id={id_attr} out of range for vocab size {vocab_size}"
                    )

            resolved_tok = tok_attr
            resolved_id = id_attr
            if resolved_tok is not None:
                if resolved_tok not in vocab:
                    raise ValueError(
                        f"Invalid {role} special token: {role_name}_token={resolved_tok!r} is not in vocabulary"
                    )
                vocab_id = vocab[resolved_tok]
                if resolved_id is not None and resolved_id != vocab_id:
                    raise ValueError(
                        f"Inconsistent {role} special token {role_name}: token {resolved_tok!r} maps to {vocab_id} "
                        f"in vocab, but {role_name}_token_id={resolved_id}"
                    )
                resolved_id = vocab_id
            elif resolved_id is not None:
                resolved_tok = id_to_token.get(resolved_id)

            if resolved_tok is not None or resolved_id is not None:
                special_roles.append((role_name, resolved_tok, resolved_id))

        raw_add_special = getattr(tokenizer, "additional_special_tokens", None)
        additional_special: Tuple[str, ...] = ()
        if raw_add_special is not None:
            if not isinstance(raw_add_special, (list, tuple)):
                raise ValueError(
                    f"Unsupported {role} tokenizer introspection: additional_special_tokens must be a list or tuple"
                )
            parsed_add: List[str] = []
            for item in raw_add_special:
                if not isinstance(item, str) or item not in vocab:
                    raise ValueError(
                        f"Invalid {role} additional_special_tokens entry {item!r}: must be a string in vocabulary"
                    )
                parsed_add.append(item)
            additional_special = tuple(parsed_add)

        chat_template = getattr(tokenizer, "chat_template", None)
        if chat_template is not None and not isinstance(chat_template, str):
            chat_template = str(chat_template)

        raw_name = getattr(tokenizer, "name_or_path", None)
        name = str(raw_name) if raw_name else f"tokenizer_{id(tokenizer)}"

        return TokenizerSpec(
            name=name,
            vocab=vocab,
            id_to_token=id_to_token,
            vocab_size=vocab_size,
            special_roles=tuple(special_roles),
            additional_special_tokens=additional_special,
            chat_template=chat_template,
            has_codec=has_codec,
        )

    @staticmethod
    def _unwrap_tokenizer_identity(tokenizer: Any) -> Any:
        """Return the underlying engine/tokenizer object for stable identity memoization."""
        engine = getattr(tokenizer, "_engine", None)
        return engine if engine is not None else tokenizer

    def _get_tokenizer_spec(self, tokenizer: Any, role: str, require_codec: bool = False) -> TokenizerSpec:
        """Return cached TokenizerSpec for a tokenizer instance, validating once."""
        tok_identity = self._unwrap_tokenizer_identity(tokenizer)
        tok_key = id(tok_identity)
        cached = self._tokenizer_specs.get(tok_key)
        if cached is not None and cached[0] is tok_identity:
            spec = cached[1]
            if require_codec and not spec.has_codec:
                raise ValueError(
                    f"Unsupported {role} tokenizer introspection: callable encode() and decode() are required"
                )
            return spec

        spec = self._inspect_tokenizer(tokenizer, role, require_codec=require_codec)
        self._tokenizer_specs[tok_key] = (tok_identity, spec)
        return spec

    @staticmethod
    def _validate_special_semantics(
        source_tokenizer: Any,
        target_tokenizer: Any,
        source_spec: TokenizerSpec,
        target_spec: TokenizerSpec,
        equal_vocab_mapping: bool,
    ) -> bool:
        """Validate special-token compatibility and return True iff special semantics are identical."""
        equal_special = (
            source_spec.special_roles == target_spec.special_roles
            and source_spec.additional_special_tokens == target_spec.additional_special_tokens
            and source_spec.chat_template == target_spec.chat_template
        )

        # Probe skip_special_tokens decoding parity on declared special token IDs if both have decode()
        if equal_special and source_spec.has_codec and target_spec.has_codec and equal_vocab_mapping:
            probe_ids = {
                tid for _, _, tid in source_spec.special_roles if tid is not None
            }
            for tok_str in source_spec.additional_special_tokens:
                probe_ids.add(source_spec.vocab[tok_str])
            for tid in sorted(probe_ids):
                try:
                    src_skip = source_tokenizer.decode([tid], skip_special_tokens=True)
                    tgt_skip = target_tokenizer.decode([tid], skip_special_tokens=True)
                    src_keep = source_tokenizer.decode([tid], skip_special_tokens=False)
                    tgt_keep = target_tokenizer.decode([tid], skip_special_tokens=False)
                except Exception as exc:
                    raise ValueError(f"Failed special-token decode verification for token ID {tid}: {exc}") from exc
                if src_skip != tgt_skip or src_keep != tgt_keep:
                    equal_special = False
                    break

        if equal_vocab_mapping and not equal_special:
            raise ValueError(
                "Incompatible special-token semantics between tokenizers with identical get_vocab() mappings"
            )

        # Even when vocabularies differ, reject conflicting special-token role assignments on the same token string
        # (e.g., source BOS token string is target EOS token string, unless that tokenizer intentionally aliases BOS/EOS).
        src_roles_by_tok: Dict[str, set] = {}
        for r_name, r_tok, _ in source_spec.special_roles:
            if r_tok is not None:
                src_roles_by_tok.setdefault(r_tok, set()).add(r_name)
        tgt_roles_by_tok: Dict[str, set] = {}
        for r_name, r_tok, _ in target_spec.special_roles:
            if r_tok is not None:
                tgt_roles_by_tok.setdefault(r_tok, set()).add(r_name)

        for shared_tok in set(src_roles_by_tok.keys()) & set(tgt_roles_by_tok.keys()):
            if src_roles_by_tok[shared_tok] != tgt_roles_by_tok[shared_tok]:
                raise ValueError(
                    f"Conflicting special-token semantics for token {shared_tok!r}: "
                    f"source roles={sorted(src_roles_by_tok[shared_tok])}, "
                    f"target roles={sorted(tgt_roles_by_tok[shared_tok])}"
                )

        return equal_special

    def _resolve_pair_spec(
        self,
        source_tokenizer: Optional['PreTrainedTokenizerBase'] = None,
        target_tokenizer: Optional['PreTrainedTokenizerBase'] = None,
    ) -> TokenizerPairSpec:
        """Resolve and memoize TokenizerPairSpec so token-to-ID mappings are compared only once per pair."""
        if source_tokenizer is None and target_tokenizer is None:
            if self._bound_pair_spec is not None:
                return self._bound_pair_spec
            raise ValueError("source_tokenizer and target_tokenizer must be provided")

        if source_tokenizer is None or target_tokenizer is None:
            raise ValueError("Both source_tokenizer and target_tokenizer must be provided")

        src_identity = self._unwrap_tokenizer_identity(source_tokenizer)
        tgt_identity = self._unwrap_tokenizer_identity(target_tokenizer)

        if (
            self._bound_pair_spec is not None
            and src_identity is self._unwrap_tokenizer_identity(self._bound_source_tokenizer)
            and tgt_identity is self._unwrap_tokenizer_identity(self._bound_target_tokenizer)
        ):
            return self._bound_pair_spec

        pair_key = (id(src_identity), id(tgt_identity))
        cached_pair = self._pair_specs.get(pair_key)
        if (
            cached_pair is not None
            and cached_pair[0] is src_identity
            and cached_pair[1] is tgt_identity
        ):
            return cached_pair[2]

        source_spec = self._get_tokenizer_spec(
            source_tokenizer, "source", require_codec=self.REQUIRES_CODEC
        )
        target_spec = self._get_tokenizer_spec(
            target_tokenizer, "target", require_codec=self.REQUIRES_CODEC
        )

        if (source_spec.vocab_size == 0) != (target_spec.vocab_size == 0):
            raise ValueError(
                f"Incompatible vocabulary sizes: source has {source_spec.vocab_size} tokens, "
                f"target has {target_spec.vocab_size} tokens"
            )

        equal_vocab_mapping = source_spec.vocab == target_spec.vocab
        equal_special_semantics = self._validate_special_semantics(
            source_tokenizer,
            target_tokenizer,
            source_spec,
            target_spec,
            equal_vocab_mapping=equal_vocab_mapping,
        )
        can_passthrough = equal_vocab_mapping and equal_special_semantics

        pair_spec = TokenizerPairSpec(
            source=source_spec,
            target=target_spec,
            equal_vocab_mapping=equal_vocab_mapping,
            equal_special_semantics=equal_special_semantics,
            can_passthrough=can_passthrough,
        )
        self._pair_specs[pair_key] = (src_identity, tgt_identity, pair_spec)
        return pair_spec

    def _validate_input_vector(
        self,
        arr: np.ndarray,
        pair_spec: TokenizerPairSpec,
        kind: str = "logits",
    ) -> np.ndarray:
        """Flatten and validate that the input vector dimension matches the source vocabulary size."""
        flattened = np.asarray(self._flatten_if_needed(arr), dtype=np.float32)
        if flattened.shape != (pair_spec.source.vocab_size,):
            raise ValueError(
                f"Source {kind} dimension ({len(flattened)}) does not match "
                f"source vocabulary size ({pair_spec.source.vocab_size})"
            )
        return flattened

    def _required_mapped_tokens(self, pair_spec: TokenizerPairSpec) -> int:
        """Determine the minimum required mapped tokens for a tokenizer pair."""
        if pair_spec.source.vocab_size == 0 and pair_spec.target.vocab_size == 0:
            return 0
        if self._explicit_min_mapped_tokens is not None:
            return self.min_mapped_tokens
        if pair_spec.source.vocab_size >= self.min_mapped_tokens:
            return self.min_mapped_tokens
        return 1

    def _validate_mapping_coverage(
        self,
        mapped_count: int,
        pair_spec: TokenizerPairSpec,
        translator_name: str,
    ) -> None:
        """Reject inadequate vocabulary overlap instead of falling back to raw token indices."""
        required = self._required_mapped_tokens(pair_spec)
        if mapped_count < required:
            raise ValueError(
                f"{translator_name}: inadequate vocabulary overlap between '{pair_spec.source.name}' "
                f"and '{pair_spec.target.name}' (mapped {mapped_count} of {pair_spec.source.vocab_size} "
                f"source tokens; minimum required is {required})"
            )

    def _make_cache_key(
        self,
        source_tokenizer: 'PreTrainedTokenizerBase',
        target_tokenizer: 'PreTrainedTokenizerBase',
        suffix: str = ""
    ) -> str:
        """Generate a cache key for a tokenizer pair that distinguishes distinct vocabularies."""
        src_identity = self._unwrap_tokenizer_identity(source_tokenizer)
        tgt_identity = self._unwrap_tokenizer_identity(target_tokenizer)
        src_name = getattr(source_tokenizer, "name_or_path", None) or f"tok_{id(src_identity)}"
        tgt_name = getattr(target_tokenizer, "name_or_path", None) or f"tok_{id(tgt_identity)}"
        base = f"{src_name}#{id(src_identity)}-to-{tgt_name}#{id(tgt_identity)}"
        return f"{base}-{suffix}" if suffix else base

    def _get_cached(self, key: str) -> Any:
        """Retrieve a value from cache if caching is enabled."""
        if self.use_cache and key in self._cache:
            return self._cache[key]
        return None

    def _set_cached(self, key: str, value: Any) -> None:
        """Store a value in cache if caching is enabled."""
        if self.use_cache:
            self._cache[key] = value

    def _flatten_if_needed(self, arr: np.ndarray) -> np.ndarray:
        """Flatten array to 1D if it has more dimensions."""
        arr = np.asarray(arr)
        if arr.ndim > 1:
            return arr.flatten()
        return arr

    def _same_vocab_size(
        self,
        source_tokenizer: 'PreTrainedTokenizerBase',
        target_tokenizer: 'PreTrainedTokenizerBase'
    ) -> bool:
        """Return True only when token-to-ID mappings and special-token semantics are identical."""
        pair_spec = self._resolve_pair_spec(source_tokenizer, target_tokenizer)
        return pair_spec.can_passthrough

    def _init_target_logits(self, size: int, fill_value: float = None) -> np.ndarray:
        """Initialize target logits array with a floor value."""
        if fill_value is None:
            fill_value = self.DEFAULT_LOGIT_FLOOR
        return np.full(size, fill_value, dtype=np.float32)

    def _init_target_probs(self, size: int) -> np.ndarray:
        """Initialize target probability array with zeros."""
        return np.zeros(size, dtype=np.float32)

    def _normalize_probs(self, probs: np.ndarray) -> np.ndarray:
        """Normalize probability array, with fallback to uniform if sum is zero."""
        total = float(np.sum(probs))
        if total > 0:
            return probs / total
        if len(probs) == 0:
            return probs
        return np.ones_like(probs) / len(probs)

    def _log_build_start(self, source_name: str, target_name: str, map_type: str) -> None:
        """Log the start of map building (respects verbosity setting)."""
        if self.verbose:
            print(f"Building {map_type} map from {source_name} to {target_name}...")
        else:
            logger.debug(f"Building {map_type} map from {source_name} to {target_name}...")

    def _log_build_complete(self, mapped: int, total: int, map_type: str) -> None:
        """Log map building completion (respects verbosity setting)."""
        if self.verbose:
            print(f"{map_type.capitalize()} map built. Mapped {mapped} of {total} tokens.")
        else:
            logger.debug(f"{map_type.capitalize()} map built. Mapped {mapped} of {total} tokens.")

    @abstractmethod
    def translate_logits(
        self,
        source_logits: np.ndarray,
        source_tokenizer: Optional['PreTrainedTokenizerBase'] = None,
        target_tokenizer: Optional['PreTrainedTokenizerBase'] = None,
    ) -> np.ndarray:
        """Translate logits from the source model's vocabulary space to the target's."""
        pass


class VocabularyIntersectionTranslator(VocabularyTranslator):
    """
    A vocabulary translator that maps only tokens whose exact surface string exists in both vocabularies.
    """

    def _prebuild_pair(
        self,
        source_tokenizer: 'PreTrainedTokenizerBase',
        target_tokenizer: 'PreTrainedTokenizerBase',
        pair_spec: TokenizerPairSpec,
    ) -> None:
        self._get_intersection_map(source_tokenizer, target_tokenizer, pair_spec)

    def _get_intersection_map(
        self,
        source_tokenizer: 'PreTrainedTokenizerBase',
        target_tokenizer: 'PreTrainedTokenizerBase',
        pair_spec: Optional[TokenizerPairSpec] = None,
    ) -> Tuple[np.ndarray, np.ndarray, int]:
        """Build and cache a validated source->target token ID mapping for shared tokens."""
        if pair_spec is None:
            pair_spec = self._resolve_pair_spec(source_tokenizer, target_tokenizer)

        cache_key = self._make_cache_key(source_tokenizer, target_tokenizer, "intersection_map")
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

        self._log_build_start(pair_spec.source.name, pair_spec.target.name, "intersection")
        source_vocab = pair_spec.source.vocab
        target_vocab = pair_spec.target.vocab
        source_ids = []
        target_ids = []
        for token_str, source_id in source_vocab.items():
            target_id = target_vocab.get(token_str)
            if target_id is not None:
                source_ids.append(source_id)
                target_ids.append(target_id)

        self._validate_mapping_coverage(len(source_ids), pair_spec, "VocabularyIntersectionTranslator")

        source_ids_arr = np.asarray(source_ids, dtype=np.int64)
        target_ids_arr = np.asarray(target_ids, dtype=np.int64)
        target_vocab_size = pair_spec.target.vocab_size

        cached_value = (source_ids_arr, target_ids_arr, target_vocab_size)
        self._set_cached(cache_key, cached_value)
        self._log_build_complete(len(source_ids_arr), pair_spec.source.vocab_size, "intersection")
        return cached_value

    def translate_logits(
        self,
        source_logits: np.ndarray,
        source_tokenizer: Optional['PreTrainedTokenizerBase'] = None,
        target_tokenizer: Optional['PreTrainedTokenizerBase'] = None,
    ) -> np.ndarray:
        """Translate logits by projecting shared tokens to their target indices."""
        pair_spec = self._resolve_pair_spec(source_tokenizer, target_tokenizer)
        src_tok = source_tokenizer if source_tokenizer is not None else self._bound_source_tokenizer
        tgt_tok = target_tokenizer if target_tokenizer is not None else self._bound_target_tokenizer
        source_logits = self._validate_input_vector(source_logits, pair_spec, kind="logits")

        if pair_spec.can_passthrough:
            return source_logits.copy()

        source_ids, target_ids, target_vocab_size = self._get_intersection_map(
            src_tok, tgt_tok, pair_spec
        )
        target_logits = self._init_target_logits(target_vocab_size)
        np.maximum.at(target_logits, target_ids, source_logits[source_ids])
        return target_logits

    def translate_probabilities(
        self,
        source_probs: np.ndarray,
        source_tokenizer: Optional['PreTrainedTokenizerBase'] = None,
        target_tokenizer: Optional['PreTrainedTokenizerBase'] = None,
    ) -> np.ndarray:
        """Translate probabilities by summing mass over shared tokens."""
        pair_spec = self._resolve_pair_spec(source_tokenizer, target_tokenizer)
        src_tok = source_tokenizer if source_tokenizer is not None else self._bound_source_tokenizer
        tgt_tok = target_tokenizer if target_tokenizer is not None else self._bound_target_tokenizer
        source_probs = self._validate_input_vector(source_probs, pair_spec, kind="probabilities")

        if pair_spec.can_passthrough:
            return source_probs.copy()

        source_ids, target_ids, target_vocab_size = self._get_intersection_map(
            src_tok, tgt_tok, pair_spec
        )
        target_probs = self._init_target_probs(target_vocab_size)
        np.add.at(target_probs, target_ids, source_probs[source_ids])
        return self._normalize_probs(target_probs)


class AligningVocabularyTranslator(VocabularyTranslator):
    """
    A translator that aligns vocabularies using surface-form decode/encode mapping.
    """

    REQUIRES_CODEC = True

    def _prebuild_pair(
        self,
        source_tokenizer: 'PreTrainedTokenizerBase',
        target_tokenizer: 'PreTrainedTokenizerBase',
        pair_spec: TokenizerPairSpec,
    ) -> None:
        self._build_alignment_map(source_tokenizer, target_tokenizer, pair_spec)

    def _build_alignment_map(
        self,
        source_tokenizer: 'PreTrainedTokenizerBase',
        target_tokenizer: 'PreTrainedTokenizerBase',
        pair_spec: Optional[TokenizerPairSpec] = None,
    ) -> Dict[int, List[int]]:
        """Build and validate a map from source token IDs to target token ID lists."""
        if pair_spec is None:
            pair_spec = self._resolve_pair_spec(source_tokenizer, target_tokenizer)

        cache_key = self._make_cache_key(source_tokenizer, target_tokenizer, "alignment")
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

        self._log_build_start(pair_spec.source.name, pair_spec.target.name, "alignment")
        source_vocab_size = pair_spec.source.vocab_size
        target_vocab_size = pair_spec.target.vocab_size
        progress_interval = 50000 if self.verbose and source_vocab_size >= 50000 else 0

        alignment_map: Dict[int, List[int]] = {}
        for source_id in range(source_vocab_size):
            if progress_interval and source_id > 0 and source_id % progress_interval == 0:
                print(f"Alignment progress: {source_id}/{source_vocab_size} tokens")
            token_str = source_tokenizer.decode([source_id], skip_special_tokens=True)
            if not token_str:
                continue
            target_ids = target_tokenizer.encode(token_str, add_special_tokens=False)
            valid_target_ids = [
                int(tid) for tid in target_ids
                if not isinstance(tid, bool) and isinstance(tid, (int, np.integer)) and 0 <= int(tid) < target_vocab_size
            ]
            if valid_target_ids:
                alignment_map[source_id] = valid_target_ids

        self._validate_mapping_coverage(len(alignment_map), pair_spec, "AligningVocabularyTranslator")

        self._set_cached(cache_key, alignment_map)
        self._log_build_complete(len(alignment_map), source_vocab_size, "alignment")
        return alignment_map

    def translate_logits(
        self,
        source_logits: np.ndarray,
        source_tokenizer: Optional['PreTrainedTokenizerBase'] = None,
        target_tokenizer: Optional['PreTrainedTokenizerBase'] = None,
    ) -> np.ndarray:
        """Translate logits by projecting them from the source to the target vocabulary space."""
        pair_spec = self._resolve_pair_spec(source_tokenizer, target_tokenizer)
        src_tok = source_tokenizer if source_tokenizer is not None else self._bound_source_tokenizer
        tgt_tok = target_tokenizer if target_tokenizer is not None else self._bound_target_tokenizer
        source_logits = self._validate_input_vector(source_logits, pair_spec, kind="logits")

        if pair_spec.can_passthrough:
            return source_logits.copy()

        alignment_map = self._build_alignment_map(src_tok, tgt_tok, pair_spec)
        target_vocab_size = pair_spec.target.vocab_size
        target_logits = self._init_target_logits(target_vocab_size)

        for source_id, target_ids in alignment_map.items():
            logit_value = source_logits[source_id]
            for target_id in target_ids:
                target_logits[target_id] = max(target_logits[target_id], logit_value)

        return target_logits

    def translate_probabilities(
        self,
        source_probs: np.ndarray,
        source_tokenizer: Optional['PreTrainedTokenizerBase'] = None,
        target_tokenizer: Optional['PreTrainedTokenizerBase'] = None,
    ) -> np.ndarray:
        """Translate a probability distribution from the source vocabulary to the target vocabulary."""
        pair_spec = self._resolve_pair_spec(source_tokenizer, target_tokenizer)
        src_tok = source_tokenizer if source_tokenizer is not None else self._bound_source_tokenizer
        tgt_tok = target_tokenizer if target_tokenizer is not None else self._bound_target_tokenizer
        source_probs = self._validate_input_vector(source_probs, pair_spec, kind="probabilities")

        if pair_spec.can_passthrough:
            return source_probs.copy()

        alignment_map = self._build_alignment_map(src_tok, tgt_tok, pair_spec)
        target_vocab_size = pair_spec.target.vocab_size
        target_probs = self._init_target_probs(target_vocab_size)

        for source_id, target_ids in alignment_map.items():
            prob = source_probs[source_id]
            if prob <= 0.0:
                continue
            share = prob / len(target_ids)
            for target_id in target_ids:
                target_probs[target_id] += share

        return self._normalize_probs(target_probs)


class SemanticMappingTranslator(VocabularyTranslator):
    """
    A translator that maps tokens between vocabularies using exact match followed by
    character n-gram similarity above a configured threshold.
    """

    def __init__(
        self,
        use_cache: bool = True,
        verbose: bool = False,
        similarity_threshold: float = 0.5,
        source_tokenizer: Optional['PreTrainedTokenizerBase'] = None,
        target_tokenizer: Optional['PreTrainedTokenizerBase'] = None,
        min_mapped_tokens: Optional[int] = None,
    ):
        self.similarity_threshold = similarity_threshold
        super().__init__(
            use_cache=use_cache,
            verbose=verbose,
            source_tokenizer=source_tokenizer,
            target_tokenizer=target_tokenizer,
            min_mapped_tokens=min_mapped_tokens,
        )

    def _prebuild_pair(
        self,
        source_tokenizer: 'PreTrainedTokenizerBase',
        target_tokenizer: 'PreTrainedTokenizerBase',
        pair_spec: TokenizerPairSpec,
    ) -> None:
        self._build_semantic_map(source_tokenizer, target_tokenizer, pair_spec)

    def _get_token_embedding(self, token: str) -> np.ndarray:
        """Create a normalized character unigram/bigram embedding for a token."""
        embedding = np.zeros(256, dtype=np.float32)

        for char in token:
            idx = ord(char) % 256
            embedding[idx] += 1.0

        for i in range(len(token) - 1):
            bigram_hash = (ord(token[i]) * 31 + ord(token[i + 1])) % 256
            embedding[bigram_hash] += 0.5

        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm

        return embedding

    def _build_semantic_map(
        self,
        source_tokenizer: 'PreTrainedTokenizerBase',
        target_tokenizer: 'PreTrainedTokenizerBase',
        pair_spec: Optional[TokenizerPairSpec] = None,
    ) -> Dict[int, int]:
        """Build and validate a semantic mapping from source to target token IDs."""
        if pair_spec is None:
            pair_spec = self._resolve_pair_spec(source_tokenizer, target_tokenizer)

        cache_key = self._make_cache_key(source_tokenizer, target_tokenizer, "semantic")
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

        self._log_build_start(pair_spec.source.name, pair_spec.target.name, "semantic")

        source_vocab = pair_spec.source.vocab
        target_vocab = pair_spec.target.vocab

        target_tokens = list(target_vocab.keys())
        target_ids = [target_vocab[t] for t in target_tokens]
        target_embeddings = (
            np.array([self._get_token_embedding(t) for t in target_tokens])
            if target_tokens
            else np.empty((0, 256), dtype=np.float32)
        )

        semantic_map: Dict[int, int] = {}
        for source_token, source_id in source_vocab.items():
            if source_token in target_vocab:
                semantic_map[source_id] = target_vocab[source_token]
                continue

            if len(target_tokens) == 0:
                continue

            source_embedding = self._get_token_embedding(source_token)
            similarities = np.dot(target_embeddings, source_embedding)

            best_idx = int(np.argmax(similarities))
            best_similarity = float(similarities[best_idx])

            if best_similarity >= self.similarity_threshold:
                semantic_map[source_id] = target_ids[best_idx]

        self._validate_mapping_coverage(len(semantic_map), pair_spec, "SemanticMappingTranslator")

        self._set_cached(cache_key, semantic_map)
        self._log_build_complete(len(semantic_map), pair_spec.source.vocab_size, "semantic")
        return semantic_map

    def translate_logits(
        self,
        source_logits: np.ndarray,
        source_tokenizer: Optional['PreTrainedTokenizerBase'] = None,
        target_tokenizer: Optional['PreTrainedTokenizerBase'] = None,
    ) -> np.ndarray:
        """Translate logits using semantic token mapping without raw-index fallback."""
        pair_spec = self._resolve_pair_spec(source_tokenizer, target_tokenizer)
        src_tok = source_tokenizer if source_tokenizer is not None else self._bound_source_tokenizer
        tgt_tok = target_tokenizer if target_tokenizer is not None else self._bound_target_tokenizer
        source_logits = self._validate_input_vector(source_logits, pair_spec, kind="logits")

        if pair_spec.can_passthrough:
            return source_logits.copy()

        semantic_map = self._build_semantic_map(src_tok, tgt_tok, pair_spec)
        target_vocab_size = pair_spec.target.vocab_size
        target_logits = self._init_target_logits(target_vocab_size)

        for source_id, target_id in semantic_map.items():
            target_logits[target_id] = max(target_logits[target_id], source_logits[source_id])

        return target_logits

    def translate_probabilities(
        self,
        source_probs: np.ndarray,
        source_tokenizer: Optional['PreTrainedTokenizerBase'] = None,
        target_tokenizer: Optional['PreTrainedTokenizerBase'] = None,
    ) -> np.ndarray:
        """Translate probabilities using semantic token mapping without raw-index fallback."""
        pair_spec = self._resolve_pair_spec(source_tokenizer, target_tokenizer)
        src_tok = source_tokenizer if source_tokenizer is not None else self._bound_source_tokenizer
        tgt_tok = target_tokenizer if target_tokenizer is not None else self._bound_target_tokenizer
        source_probs = self._validate_input_vector(source_probs, pair_spec, kind="probabilities")

        if pair_spec.can_passthrough:
            return source_probs.copy()

        semantic_map = self._build_semantic_map(src_tok, tgt_tok, pair_spec)
        target_vocab_size = pair_spec.target.vocab_size
        target_probs = self._init_target_probs(target_vocab_size)

        for source_id, target_id in semantic_map.items():
            prob = source_probs[source_id]
            if prob > 0.0:
                target_probs[target_id] += prob

        return self._normalize_probs(target_probs)


class SubwordDecompositionTranslator(VocabularyTranslator):
    """
    A translator that handles vocabulary mismatches by decomposing source tokens
    into target subword components.
    """

    REQUIRES_CODEC = True

    def _prebuild_pair(
        self,
        source_tokenizer: 'PreTrainedTokenizerBase',
        target_tokenizer: 'PreTrainedTokenizerBase',
        pair_spec: TokenizerPairSpec,
    ) -> None:
        self._build_decomposition_map(source_tokenizer, target_tokenizer, pair_spec)

    def _decompose_token(self, token: str, target_tokenizer: 'PreTrainedTokenizerBase') -> List[int]:
        """Decompose a token string into target tokenizer's subword IDs."""
        return target_tokenizer.encode(token, add_special_tokens=False)

    def _build_decomposition_map(
        self,
        source_tokenizer: 'PreTrainedTokenizerBase',
        target_tokenizer: 'PreTrainedTokenizerBase',
        pair_spec: Optional[TokenizerPairSpec] = None,
    ) -> Dict[int, List[Tuple[int, float]]]:
        """Build and validate a map from source token IDs to weighted target subword IDs."""
        if pair_spec is None:
            pair_spec = self._resolve_pair_spec(source_tokenizer, target_tokenizer)

        cache_key = self._make_cache_key(source_tokenizer, target_tokenizer, "subword")
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

        self._log_build_start(pair_spec.source.name, pair_spec.target.name, "subword decomposition")

        source_vocab = pair_spec.source.vocab
        target_vocab_size = pair_spec.target.vocab_size
        decomposition_map: Dict[int, List[Tuple[int, float]]] = {}

        for _, source_id in source_vocab.items():
            token_str = source_tokenizer.decode([source_id], skip_special_tokens=True)
            if not token_str or token_str.isspace():
                continue

            target_subword_ids = self._decompose_token(token_str, target_tokenizer)
            valid_subwords = [
                int(sid) for sid in target_subword_ids
                if not isinstance(sid, bool) and isinstance(sid, (int, np.integer)) and 0 <= int(sid) < target_vocab_size
            ]
            if valid_subwords:
                weighted_subwords = [
                    (subword_id, 1.0 / (i + 1))
                    for i, subword_id in enumerate(valid_subwords)
                ]
                decomposition_map[source_id] = weighted_subwords

        self._validate_mapping_coverage(
            len(decomposition_map), pair_spec, "SubwordDecompositionTranslator"
        )

        self._set_cached(cache_key, decomposition_map)
        self._log_build_complete(len(decomposition_map), pair_spec.source.vocab_size, "subword decomposition")
        return decomposition_map

    def translate_logits(
        self,
        source_logits: np.ndarray,
        source_tokenizer: Optional['PreTrainedTokenizerBase'] = None,
        target_tokenizer: Optional['PreTrainedTokenizerBase'] = None,
    ) -> np.ndarray:
        """Translate logits using subword decomposition without raw-index fallback."""
        pair_spec = self._resolve_pair_spec(source_tokenizer, target_tokenizer)
        src_tok = source_tokenizer if source_tokenizer is not None else self._bound_source_tokenizer
        tgt_tok = target_tokenizer if target_tokenizer is not None else self._bound_target_tokenizer
        source_logits = self._validate_input_vector(source_logits, pair_spec, kind="logits")

        if pair_spec.can_passthrough:
            return source_logits.copy()

        decomposition_map = self._build_decomposition_map(src_tok, tgt_tok, pair_spec)
        target_vocab_size = pair_spec.target.vocab_size
        target_logits = self._init_target_logits(target_vocab_size)

        for source_id, weighted_subwords in decomposition_map.items():
            logit_value = source_logits[source_id]
            for target_id, weight in weighted_subwords:
                weighted_logit = logit_value * weight
                target_logits[target_id] = max(target_logits[target_id], weighted_logit)

        return target_logits

    def translate_probabilities(
        self,
        source_probs: np.ndarray,
        source_tokenizer: Optional['PreTrainedTokenizerBase'] = None,
        target_tokenizer: Optional['PreTrainedTokenizerBase'] = None,
    ) -> np.ndarray:
        """Translate probabilities using subword decomposition without raw-index fallback."""
        pair_spec = self._resolve_pair_spec(source_tokenizer, target_tokenizer)
        src_tok = source_tokenizer if source_tokenizer is not None else self._bound_source_tokenizer
        tgt_tok = target_tokenizer if target_tokenizer is not None else self._bound_target_tokenizer
        source_probs = self._validate_input_vector(source_probs, pair_spec, kind="probabilities")

        if pair_spec.can_passthrough:
            return source_probs.copy()

        decomposition_map = self._build_decomposition_map(src_tok, tgt_tok, pair_spec)
        target_vocab_size = pair_spec.target.vocab_size
        target_probs = self._init_target_probs(target_vocab_size)

        for source_id, weighted_subwords in decomposition_map.items():
            prob = source_probs[source_id]
            if prob <= 0.0:
                continue
            weight_sum = sum(w for _, w in weighted_subwords)
            if weight_sum <= 0.0:
                continue
            for target_id, weight in weighted_subwords:
                target_probs[target_id] += prob * (weight / weight_sum)

        return self._normalize_probs(target_probs)


class FallbackToUnkTranslator(VocabularyTranslator):
    """
    A translator that preserves shared tokens and maps unknown source tokens to
    the target tokenizer's explicit UNK token.
    """

    # Common UNK token variants
    UNK_VARIANTS = ["<unk>", "[UNK]", "<UNK>", "unk", "<|unk|>"]

    def __init__(
        self,
        unk_token: str = "<unk>",
        use_cache: bool = True,
        verbose: bool = False,
        source_tokenizer: Optional['PreTrainedTokenizerBase'] = None,
        target_tokenizer: Optional['PreTrainedTokenizerBase'] = None,
        min_mapped_tokens: Optional[int] = None,
    ):
        self.unk_token = unk_token
        super().__init__(
            use_cache=use_cache,
            verbose=verbose,
            source_tokenizer=source_tokenizer,
            target_tokenizer=target_tokenizer,
            min_mapped_tokens=min_mapped_tokens,
        )

    def _prebuild_pair(
        self,
        source_tokenizer: 'PreTrainedTokenizerBase',
        target_tokenizer: 'PreTrainedTokenizerBase',
        pair_spec: TokenizerPairSpec,
    ) -> None:
        self._build_mapping_with_unk(source_tokenizer, target_tokenizer, pair_spec)

    def _find_unk_token_id(self, tokenizer: 'PreTrainedTokenizerBase') -> int:
        """Find the explicit UNK token ID in the tokenizer's vocabulary, or raise ValueError."""
        spec = self._get_tokenizer_spec(tokenizer, "target", require_codec=False)
        vocab = spec.vocab

        if self.unk_token in vocab:
            return vocab[self.unk_token]

        if hasattr(tokenizer, "unk_token") and getattr(tokenizer, "unk_token") in vocab:
            return vocab[getattr(tokenizer, "unk_token")]

        unk_id_attr = getattr(tokenizer, "unk_token_id", None)
        if (
            unk_id_attr is not None
            and not isinstance(unk_id_attr, bool)
            and isinstance(unk_id_attr, (int, np.integer))
            and 0 <= int(unk_id_attr) < spec.vocab_size
        ):
            return int(unk_id_attr)

        for variant in self.UNK_VARIANTS:
            if variant in vocab:
                return vocab[variant]

        raise ValueError(
            f"Target tokenizer '{spec.name}' does not define a valid UNK token; "
            "refusing to fall back to token ID 0"
        )

    def _build_mapping_with_unk(
        self,
        source_tokenizer: 'PreTrainedTokenizerBase',
        target_tokenizer: 'PreTrainedTokenizerBase',
        pair_spec: Optional[TokenizerPairSpec] = None,
    ) -> Tuple[Dict[int, int], Optional[int]]:
        """Build a validated mapping from source to target IDs with explicit UNK fallback."""
        if pair_spec is None:
            pair_spec = self._resolve_pair_spec(source_tokenizer, target_tokenizer)

        cache_key = self._make_cache_key(source_tokenizer, target_tokenizer, "unk")
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

        self._log_build_start(pair_spec.source.name, pair_spec.target.name, "UNK fallback")

        source_vocab = pair_spec.source.vocab
        target_vocab = pair_spec.target.vocab

        direct_matches = 0
        unmapped_ids: List[int] = []
        mapping: Dict[int, int] = {}

        for source_token, source_id in source_vocab.items():
            if source_token in target_vocab:
                mapping[source_id] = target_vocab[source_token]
                direct_matches += 1
            else:
                unmapped_ids.append(source_id)

        self._validate_mapping_coverage(direct_matches, pair_spec, "FallbackToUnkTranslator")

        unk_id: Optional[int] = None
        if unmapped_ids:
            unk_id = self._find_unk_token_id(target_tokenizer)
            for source_id in unmapped_ids:
                mapping[source_id] = unk_id
        else:
            try:
                unk_id = self._find_unk_token_id(target_tokenizer)
            except ValueError:
                unk_id = None

        result = (mapping, unk_id)
        self._set_cached(cache_key, result)

        unk_count = len(unmapped_ids)
        if self.verbose:
            logger.info(f"UNK fallback map built. {direct_matches} direct, {unk_count} to UNK.")
        else:
            logger.debug(f"UNK fallback map built. {direct_matches} direct, {unk_count} to UNK.")
        return result

    def translate_logits(
        self,
        source_logits: np.ndarray,
        source_tokenizer: Optional['PreTrainedTokenizerBase'] = None,
        target_tokenizer: Optional['PreTrainedTokenizerBase'] = None,
    ) -> np.ndarray:
        """Translate logits, mapping unknown tokens to explicit UNK without raw-index fallback."""
        pair_spec = self._resolve_pair_spec(source_tokenizer, target_tokenizer)
        src_tok = source_tokenizer if source_tokenizer is not None else self._bound_source_tokenizer
        tgt_tok = target_tokenizer if target_tokenizer is not None else self._bound_target_tokenizer
        source_logits = self._validate_input_vector(source_logits, pair_spec, kind="logits")

        if pair_spec.can_passthrough:
            return source_logits.copy()

        mapping, unk_id = self._build_mapping_with_unk(src_tok, tgt_tok, pair_spec)
        target_vocab_size = pair_spec.target.vocab_size
        target_logits = self._init_target_logits(target_vocab_size)

        unk_logits: List[float] = []
        for source_id, target_id in mapping.items():
            logit_value = float(source_logits[source_id])
            if unk_id is not None and target_id == unk_id and pair_spec.source.id_to_token[source_id] not in pair_spec.target.vocab:
                unk_logits.append(logit_value)
            elif target_id < target_vocab_size:
                target_logits[target_id] = max(target_logits[target_id], logit_value)

        if unk_logits and unk_id is not None and unk_id < target_vocab_size:
            max_unk = max(unk_logits)
            combined_unk = max_unk + float(np.log(len(unk_logits)))
            target_logits[unk_id] = max(target_logits[unk_id], combined_unk)

        return target_logits

    def translate_probabilities(
        self,
        source_probs: np.ndarray,
        source_tokenizer: Optional['PreTrainedTokenizerBase'] = None,
        target_tokenizer: Optional['PreTrainedTokenizerBase'] = None,
    ) -> np.ndarray:
        """Translate probabilities, accumulating unmapped tokens into explicit UNK."""
        pair_spec = self._resolve_pair_spec(source_tokenizer, target_tokenizer)
        src_tok = source_tokenizer if source_tokenizer is not None else self._bound_source_tokenizer
        tgt_tok = target_tokenizer if target_tokenizer is not None else self._bound_target_tokenizer
        source_probs = self._validate_input_vector(source_probs, pair_spec, kind="probabilities")

        if pair_spec.can_passthrough:
            return source_probs.copy()

        mapping, _ = self._build_mapping_with_unk(src_tok, tgt_tok, pair_spec)
        target_vocab_size = pair_spec.target.vocab_size
        target_probs = self._init_target_probs(target_vocab_size)

        for source_id, target_id in mapping.items():
            prob = source_probs[source_id]
            if prob > 0.0 and target_id < target_vocab_size:
                target_probs[target_id] += prob

        return self._normalize_probs(target_probs)
