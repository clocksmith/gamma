"""
Debate-adjudicated Distillation (DaD) training-data importer for Gamma.

Connects verified MoM/DaD records (`dadVersion: 0`) to Gamma's distillation
workflows with:
1. Provenance verification via `verify_dad_bundle` (Step 2 verifier).
2. Content-addressed proposal & request payload resolution (`proposalHash`, `inputHash`).
3. Explicit training-weight-to-loss semantics (`winner_sft`, `weighted_sft`,
   `contrastive_preference`).
4. Explicit evaluation/benchmark contamination checks (exact normalized text,
   SHA-256 digest, and token n-gram overlap).
5. Provenance accounting separating `available_bundles` from `accepted_bundles`
   and `emitted_rows`.
"""

from __future__ import annotations

import hashlib
import json
import math
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple

from projects.distillation.shared.dad_schema import (
    DadValidationError,
    VerifiedDadBundle,
    canonical_json,
    sha256_json,
    verify_dad_bundle,
)

SUPPORTED_LOSS_MODES: Tuple[str, ...] = (
    "winner_sft",
    "weighted_sft",
    "contrastive_preference",
)


class DadImportError(ValueError):
    """Raised when a DaD bundle fails training-weight semantics, target compatibility, or contamination gates."""


def normalize_text_for_contamination(text: str) -> str:
    """Normalize text for exact and n-gram contamination checks."""
    if not isinstance(text, str):
        return ""
    folded = unicodedata.normalize("NFKC", text).casefold()
    return " ".join(folded.split()).strip()


def tokenize_words_for_contamination(text: str) -> Tuple[str, ...]:
    """Extract normalized alphanumeric word tokens for n-gram overlap detection."""
    norm = normalize_text_for_contamination(text)
    if not norm:
        return ()
    words: List[str] = []
    buf: List[str] = []
    for ch in norm:
        cat = unicodedata.category(ch)
        if cat.startswith("L") or cat.startswith("N") or ch.isalnum():
            buf.append(ch)
        else:
            if buf:
                words.append("".join(buf))
                buf = []
    if buf:
        words.append("".join(buf))
    return tuple(words)


def _extract_ngrams(words: Sequence[str], n: int) -> Set[Tuple[str, ...]]:
    if len(words) == 0:
        return set()
    if len(words) < n:
        return {tuple(words)}
    return {tuple(words[i : i + n]) for i in range(len(words) - n + 1)}


@dataclass(frozen=True)
class EvalBenchmarkEntry:
    """Normalized benchmark reference entry used for decontamination."""

    entry_id: str
    normalized_text: str
    text_sha256: str
    words: Tuple[str, ...]
    ngrams: frozenset[Tuple[str, ...]]


class ContaminationFilter:
    """Rejects DaD examples whose prompt or proposal text overlaps evaluation benchmarks."""

    def __init__(
        self,
        eval_texts: Iterable[str] = (),
        *,
        ngram_size: int = 5,
        max_ngram_overlap: float = 0.8,
        min_tokens_for_ngram_check: int = 5,
    ):
        if isinstance(ngram_size, bool) or not isinstance(ngram_size, int) or ngram_size < 1:
            raise ValueError("ngram_size must be a positive integer")
        if (
            isinstance(max_ngram_overlap, bool)
            or not isinstance(max_ngram_overlap, (int, float))
            or not (0.0 < float(max_ngram_overlap) <= 1.0)
        ):
            raise ValueError("max_ngram_overlap must be in (0.0, 1.0]")
        if (
            isinstance(min_tokens_for_ngram_check, bool)
            or not isinstance(min_tokens_for_ngram_check, int)
            or min_tokens_for_ngram_check < 1
        ):
            raise ValueError("min_tokens_for_ngram_check must be a positive integer")

        self.ngram_size = ngram_size
        self.max_ngram_overlap = float(max_ngram_overlap)
        self.min_tokens_for_ngram_check = min_tokens_for_ngram_check

        self._entries: List[EvalBenchmarkEntry] = []
        self._exact_hashes: Dict[str, str] = {}

        for idx, raw_text in enumerate(eval_texts):
            if not isinstance(raw_text, str):
                continue
            norm = normalize_text_for_contamination(raw_text)
            if not norm:
                continue
            digest = hashlib.sha256(norm.encode("utf-8")).hexdigest()
            entry_id = f"eval_{idx}"
            words = tokenize_words_for_contamination(norm)
            ngrams = frozenset(_extract_ngrams(words, self.ngram_size))
            entry = EvalBenchmarkEntry(
                entry_id=entry_id,
                normalized_text=norm,
                text_sha256=digest,
                words=words,
                ngrams=ngrams,
            )
            self._entries.append(entry)
            self._exact_hashes.setdefault(digest, entry_id)

    @classmethod
    def from_jsonl_files(
        cls,
        paths: Sequence[Path | str],
        *,
        text_keys: Sequence[str] = ("prompt", "source", "query", "target", "target_pos", "reference", "completion"),
        ngram_size: int = 5,
        max_ngram_overlap: float = 0.8,
        min_tokens_for_ngram_check: int = 5,
    ) -> "ContaminationFilter":
        """Build a ContaminationFilter from one or more evaluation JSONL files."""
        collected: List[str] = []
        for raw_path in paths:
            path = Path(raw_path)
            if not path.is_file():
                raise DadImportError(f"Evaluation benchmark file does not exist: {path}")
            with path.open("r", encoding="utf-8") as handle:
                for line_no, line in enumerate(handle, start=1):
                    stripped = line.strip()
                    if not stripped:
                        continue
                    try:
                        row = json.loads(stripped)
                    except Exception as exc:
                        raise DadImportError(
                            f"Invalid JSON in evaluation file {path}:{line_no}: {exc}"
                        ) from exc
                    if not isinstance(row, Mapping):
                        raise DadImportError(
                            f"Evaluation row in {path}:{line_no} must be a JSON object"
                        )
                    for key in text_keys:
                        val = row.get(key)
                        if isinstance(val, str) and val.strip():
                            collected.append(val)
        return cls(
            collected,
            ngram_size=ngram_size,
            max_ngram_overlap=max_ngram_overlap,
            min_tokens_for_ngram_check=min_tokens_for_ngram_check,
        )

    def check_text(self, text: str, field_label: str) -> Optional[str]:
        """Return a contamination reason string if `text` overlaps the evaluation set, else None."""
        norm = normalize_text_for_contamination(text)
        if not norm or not self._entries:
            return None

        digest = hashlib.sha256(norm.encode("utf-8")).hexdigest()
        if digest in self._exact_hashes:
            return (
                f"Evaluation contamination on {field_label}: exact normalized match with "
                f"{self._exact_hashes[digest]} (sha256={digest[:12]})"
            )

        words = tokenize_words_for_contamination(norm)
        if len(words) < self.min_tokens_for_ngram_check:
            return None

        candidate_ngrams = _extract_ngrams(words, self.ngram_size)
        if not candidate_ngrams:
            return None

        for entry in self._entries:
            if len(entry.words) < self.min_tokens_for_ngram_check or not entry.ngrams:
                continue
            shared = len(candidate_ngrams & entry.ngrams)
            if shared == 0:
                continue
            containment = shared / float(min(len(candidate_ngrams), len(entry.ngrams)))
            if containment >= self.max_ngram_overlap:
                return (
                    f"Evaluation contamination on {field_label}: {self.ngram_size}-gram overlap "
                    f"{containment:.2f} >= {self.max_ngram_overlap:.2f} with {entry.entry_id}"
                )
        return None


@dataclass(frozen=True)
class DadWeightSemanticsConfig:
    """Explicit configuration for mapping DaD adjudication weights to training examples."""

    loss_mode: str
    min_winner_weight: float = 1e-6
    min_proposal_weight: float = 0.05
    min_weight_margin: float = 0.05
    max_rejected_weight_in_sft: float = 0.0
    expected_student_family: Optional[str] = None
    expected_student_adapter_id: Optional[str] = None
    emit_translation_compat: bool = False
    default_src_lang: str = "en"
    default_tgt_lang: str = "en"

    def __post_init__(self) -> None:
        if self.loss_mode not in SUPPORTED_LOSS_MODES:
            raise DadImportError(
                f"Unsupported loss_mode {self.loss_mode!r}; must be one of {SUPPORTED_LOSS_MODES}"
            )
        for attr_name in (
            "min_winner_weight",
            "min_proposal_weight",
            "min_weight_margin",
            "max_rejected_weight_in_sft",
        ):
            val = getattr(self, attr_name)
            if isinstance(val, bool) or not isinstance(val, (int, float)) or not math.isfinite(val) or val < 0.0:
                raise DadImportError(f"{attr_name} must be a finite non-negative number, got {val!r}")


@dataclass(frozen=True)
class DadRejectionRecord:
    """Provenance record for a rejected DaD bundle."""

    bundle_index: int
    mom_transcript_root: Optional[str]
    stage: str
    reason: str


@dataclass(frozen=True)
class DadImportResult:
    """Normalized output of a DaD import batch, keeping available vs. used counts explicit."""

    loss_mode: str
    available_bundles: int
    accepted_bundles: int
    rejected_bundles: int
    emitted_rows: Tuple[Dict[str, Any], ...]
    rejections: Tuple[DadRejectionRecord, ...]
    rows_sha256: str


def _extract_request_prompt(verified: VerifiedDadBundle) -> Tuple[str, str, str]:
    """Extract (prompt_text, src_lang, tgt_lang) from a verified bundle's request payload."""
    if verified.request_payload is None:
        raise DadImportError(
            f"Bundle {verified.mom_transcript_root} is missing resolved 'request' payload"
        )
    req = verified.request_payload
    prompt = req.get("prompt")
    if prompt is None:
        prompt = req.get("source")
    if prompt is None:
        prompt = req.get("input")
    if not isinstance(prompt, str) or not prompt.strip():
        raise DadImportError(
            f"Bundle {verified.mom_transcript_root} request payload must contain a non-empty 'prompt' or 'source' string"
        )
    src_lang = str(req.get("src_lang") or req.get("source_lang") or "").strip()
    tgt_lang = str(req.get("tgt_lang") or req.get("target_lang") or "").strip()
    return prompt, src_lang, tgt_lang


def _extract_proposal_text(
    verified: VerifiedDadBundle,
    proposal_hash: str,
) -> str:
    """Resolve and validate the text completion of a proposal payload."""
    if proposal_hash not in verified.resolved_proposals:
        raise DadImportError(
            f"Missing resolved proposal payload for {proposal_hash} in bundle {verified.mom_transcript_root}"
        )
    payload = verified.resolved_proposals[proposal_hash]
    if isinstance(payload, str):
        text = payload
    elif isinstance(payload, Mapping):
        raw_text = payload.get("text")
        if raw_text is None:
            raw_text = payload.get("completion")
        if raw_text is None:
            raw_text = payload.get("output")
        if not isinstance(raw_text, str):
            raise DadImportError(
                f"Proposal {proposal_hash} object payload must contain a string 'text'/'completion'/'output' field"
            )
        text = raw_text
    else:
        raise DadImportError(
            f"Proposal {proposal_hash} payload must be a string or object with text field, got {type(payload).__name__}"
        )

    if not text.strip():
        raise DadImportError(f"Proposal {proposal_hash} resolved to empty text")
    return text


def _validate_student_target(
    verified: VerifiedDadBundle,
    config: DadWeightSemanticsConfig,
) -> None:
    target = verified.export_row.student_target
    if (
        config.expected_student_family is not None
        and target.family != config.expected_student_family
    ):
        raise DadImportError(
            f"Student target family mismatch: bundle targets '{target.family}', "
            f"importer expects '{config.expected_student_family}'"
        )
    if (
        config.expected_student_adapter_id is not None
        and target.adapter_id != config.expected_student_adapter_id
    ):
        raise DadImportError(
            f"Student target adapterId mismatch: bundle targets '{target.adapter_id}', "
            f"importer expects '{config.expected_student_adapter_id}'"
        )


def _build_training_rows_for_bundle(
    verified: VerifiedDadBundle,
    config: DadWeightSemanticsConfig,
    contamination_filter: Optional[ContaminationFilter],
) -> List[Dict[str, Any]]:
    """Apply student-target, contamination, and weight-to-loss semantics to a verified DaD bundle."""
    _validate_student_target(verified, config)

    prompt_text, req_src_lang, req_tgt_lang = _extract_request_prompt(verified)
    src_lang = req_src_lang or config.default_src_lang
    tgt_lang = req_tgt_lang or config.default_tgt_lang

    if contamination_filter is not None:
        prompt_hit = contamination_filter.check_text(prompt_text, "request.prompt")
        if prompt_hit is not None:
            raise DadImportError(prompt_hit)

    # Resolve all proposal texts and check every proposal text against contamination filter
    proposal_texts: Dict[str, str] = {}
    for prop_hash in verified.proposals_by_hash.keys():
        text = _extract_proposal_text(verified, prop_hash)
        if contamination_filter is not None:
            prop_hit = contamination_filter.check_text(text, f"proposal[{prop_hash}]")
            if prop_hit is not None:
                raise DadImportError(prop_hit)
        proposal_texts[prop_hash] = text

    weights = verified.weights_by_proposal_hash
    total_raw_weight = sum(weights.values())
    if total_raw_weight <= 0.0:
        raise DadImportError(
            f"Total distillation weight across proposals must be positive, got {total_raw_weight}"
        )

    winner_hash = verified.adjudication.winner_proposal_hash
    winner_raw_weight = weights.get(winner_hash, 0.0)
    if winner_raw_weight < config.min_winner_weight or winner_raw_weight <= 0.0:
        raise DadImportError(
            f"Winner proposal {winner_hash} weight ({winner_raw_weight}) is below min_winner_weight "
            f"({config.min_winner_weight})"
        )

    rejected_set = set(verified.rejected_proposal_hashes)
    for rej_hash in rejected_set:
        rej_w = weights.get(rej_hash, 0.0)
        if config.loss_mode in ("winner_sft", "weighted_sft") and rej_w > config.max_rejected_weight_in_sft:
            raise DadImportError(
                f"Rejected proposal {rej_hash} carries weight {rej_w} > max_rejected_weight_in_sft "
                f"({config.max_rejected_weight_in_sft}) in {config.loss_mode} mode"
            )

    # Winner must have the strictly highest or tied-highest weight among all proposals
    max_weight = max(weights.values())
    if winner_raw_weight + 1e-12 < max_weight:
        raise DadImportError(
            f"Winner proposal {winner_hash} weight ({winner_raw_weight}) is less than max proposal weight ({max_weight})"
        )

    base_provenance = {
        "dad_version": verified.export_row.dad_version,
        "mom_transcript_root": verified.mom_transcript_root,
        "winner_proposal_hash": winner_hash,
        "winner_substrate_id": verified.adjudication.winner_substrate_id,
        "teacher_set_hash": verified.export_row.teacher_set_hash,
        "distillation_weights_hash": verified.adjudication.distillation_weights_hash,
        "score_vector_hash": verified.adjudication.score_vector_hash,
        "student_target": {
            "family": verified.export_row.student_target.family,
            "adapterId": verified.export_row.student_target.adapter_id,
        },
        "loss_mode": config.loss_mode,
    }

    rows: List[Dict[str, Any]] = []

    if config.loss_mode == "winner_sft":
        norm_weight = winner_raw_weight / total_raw_weight
        winner_prop = verified.proposals_by_hash[winner_hash]
        winner_text = proposal_texts[winner_hash]
        row: Dict[str, Any] = {
            **base_provenance,
            "row_id": sha256_json(
                {
                    "momTranscriptRoot": verified.mom_transcript_root,
                    "lossMode": config.loss_mode,
                    "proposalHash": winner_hash,
                }
            ),
            "proposal_hash": winner_hash,
            "substrate_id": winner_prop.substrate_id,
            "substrate_transcript_root": winner_prop.substrate_transcript_root,
            "raw_distillation_weight": winner_raw_weight,
            "sample_weight": norm_weight,
            "prompt": prompt_text,
            "completion": winner_text,
            "target_pos": winner_text,
        }
        if config.emit_translation_compat:
            row.update(
                {
                    "src_lang": src_lang,
                    "tgt_lang": tgt_lang,
                    "pair": f"{src_lang}-{tgt_lang}",
                    "source": prompt_text,
                    "target_neg": "",
                    "lang": tgt_lang,
                    "query": prompt_text,
                    "pos": winner_text,
                    "neg": "",
                }
            )
        rows.append(row)
        return rows

    if config.loss_mode == "weighted_sft":
        eligible: List[Tuple[str, float]] = []
        for w_entry in verified.adjudication.distillation_weights:
            if w_entry.proposal_hash in rejected_set:
                continue
            if w_entry.weight >= config.min_proposal_weight and w_entry.weight > 0.0:
                eligible.append((w_entry.proposal_hash, w_entry.weight))

        if not eligible:
            raise DadImportError(
                f"No non-rejected proposals met min_proposal_weight={config.min_proposal_weight}"
            )
        eligible_sum = sum(w for _, w in eligible)
        for prop_hash, raw_w in eligible:
            prop = verified.proposals_by_hash[prop_hash]
            text = proposal_texts[prop_hash]
            norm_w = raw_w / eligible_sum
            row = {
                **base_provenance,
                "row_id": sha256_json(
                    {
                        "momTranscriptRoot": verified.mom_transcript_root,
                        "lossMode": config.loss_mode,
                        "proposalHash": prop_hash,
                    }
                ),
                "proposal_hash": prop_hash,
                "substrate_id": prop.substrate_id,
                "substrate_transcript_root": prop.substrate_transcript_root,
                "is_winner": prop_hash == winner_hash,
                "raw_distillation_weight": raw_w,
                "sample_weight": norm_w,
                "prompt": prompt_text,
                "completion": text,
                "target_pos": text,
            }
            if config.emit_translation_compat:
                row.update(
                    {
                        "src_lang": src_lang,
                        "tgt_lang": tgt_lang,
                        "pair": f"{src_lang}-{tgt_lang}",
                        "source": prompt_text,
                        "target_neg": "",
                        "lang": tgt_lang,
                        "query": prompt_text,
                        "pos": text,
                        "neg": "",
                    }
                )
            rows.append(row)
        return rows

    # config.loss_mode == "contrastive_preference"
    winner_prop = verified.proposals_by_hash[winner_hash]
    winner_text = proposal_texts[winner_hash]
    winner_norm_w = winner_raw_weight / total_raw_weight

    for w_entry in verified.adjudication.distillation_weights:
        neg_hash = w_entry.proposal_hash
        if neg_hash == winner_hash:
            continue
        neg_raw_w = w_entry.weight
        raw_margin = winner_raw_weight - neg_raw_w
        if raw_margin < config.min_weight_margin:
            continue
        neg_text = proposal_texts[neg_hash]
        if normalize_text_for_contamination(neg_text) == normalize_text_for_contamination(winner_text):
            continue
        neg_prop = verified.proposals_by_hash[neg_hash]
        neg_norm_w = neg_raw_w / total_raw_weight
        norm_margin = winner_norm_w - neg_norm_w

        row = {
            **base_provenance,
            "row_id": sha256_json(
                {
                    "momTranscriptRoot": verified.mom_transcript_root,
                    "lossMode": config.loss_mode,
                    "posProposalHash": winner_hash,
                    "negProposalHash": neg_hash,
                }
            ),
            "pos_proposal_hash": winner_hash,
            "pos_substrate_id": winner_prop.substrate_id,
            "pos_substrate_transcript_root": winner_prop.substrate_transcript_root,
            "neg_proposal_hash": neg_hash,
            "neg_substrate_id": neg_prop.substrate_id,
            "neg_substrate_transcript_root": neg_prop.substrate_transcript_root,
            "neg_explicitly_rejected": neg_hash in rejected_set,
            "pos_raw_weight": winner_raw_weight,
            "neg_raw_weight": neg_raw_w,
            "raw_weight_margin": raw_margin,
            "sample_weight": norm_margin,
            "prompt": prompt_text,
            "chosen": winner_text,
            "rejected": neg_text,
            "target_pos": winner_text,
            "target_neg": neg_text,
        }
        if config.emit_translation_compat:
            row.update(
                {
                    "src_lang": src_lang,
                    "tgt_lang": tgt_lang,
                    "pair": f"{src_lang}-{tgt_lang}",
                    "source": prompt_text,
                    "lang": tgt_lang,
                    "query": prompt_text,
                    "pos": winner_text,
                    "neg": neg_text,
                }
            )
        rows.append(row)

    if not rows:
        raise DadImportError(
            f"Bundle {verified.mom_transcript_root} produced no valid contrastive preference pairs "
            f"meeting min_weight_margin={config.min_weight_margin} with distinct completion text"
        )
    return rows


def import_dad_bundles(
    bundles: Sequence[Mapping[str, Any]],
    *,
    config: DadWeightSemanticsConfig,
    contamination_filter: Optional[ContaminationFilter] = None,
    strict: bool = True,
) -> DadImportResult:
    """Verify and import a sequence of DaD bundles into deterministic Gamma training rows.

    When `strict=True`, any invalid, incompatible, or contaminated bundle raises
    `DadValidationError` or `DadImportError`. When `strict=False`, rejected bundles
    are recorded in `result.rejections` while valid bundles are emitted, keeping
    `available_bundles` distinct from `accepted_bundles`.
    """
    if not isinstance(config, DadWeightSemanticsConfig):
        raise DadImportError("config must be an instance of DadWeightSemanticsConfig")

    emitted_rows: List[Dict[str, Any]] = []
    rejections: List[DadRejectionRecord] = []
    seen_roots: Set[str] = set()
    accepted_count = 0

    for idx, raw_bundle in enumerate(bundles):
        raw_root: Optional[str] = None
        if isinstance(raw_bundle, Mapping):
            dad_part = raw_bundle.get("dad")
            if isinstance(dad_part, Mapping) and isinstance(dad_part.get("momTranscriptRoot"), str):
                raw_root = dad_part["momTranscriptRoot"]
            elif isinstance(raw_bundle.get("momTranscriptRoot"), str):
                raw_root = raw_bundle["momTranscriptRoot"]

        try:
            verified = verify_dad_bundle(
                raw_bundle,
                require_accepted=True,
                require_proposal_payloads=True,
            )
            if verified.mom_transcript_root in seen_roots:
                raise DadImportError(
                    f"Duplicate momTranscriptRoot in import batch: {verified.mom_transcript_root}"
                )
        except (DadValidationError, DadImportError) as exc:
            if strict:
                raise
            rejections.append(
                DadRejectionRecord(
                    bundle_index=idx,
                    mom_transcript_root=raw_root,
                    stage="schema_and_provenance",
                    reason=str(exc),
                )
            )
            continue

        try:
            bundle_rows = _build_training_rows_for_bundle(
                verified,
                config=config,
                contamination_filter=contamination_filter,
            )
        except DadImportError as exc:
            if strict:
                raise
            rejections.append(
                DadRejectionRecord(
                    bundle_index=idx,
                    mom_transcript_root=verified.mom_transcript_root,
                    stage="semantics_and_decontamination",
                    reason=str(exc),
                )
            )
            continue

        seen_roots.add(verified.mom_transcript_root)
        accepted_count += 1
        emitted_rows.extend(bundle_rows)

    rows_digest = sha256_json(emitted_rows)
    return DadImportResult(
        loss_mode=config.loss_mode,
        available_bundles=len(bundles),
        accepted_bundles=accepted_count,
        rejected_bundles=len(rejections),
        emitted_rows=tuple(emitted_rows),
        rejections=tuple(rejections),
        rows_sha256=rows_digest,
    )


def import_dad_jsonl(
    input_path: Path | str,
    output_path: Optional[Path | str] = None,
    *,
    config: DadWeightSemanticsConfig,
    contamination_filter: Optional[ContaminationFilter] = None,
    strict: bool = True,
) -> DadImportResult:
    """Read DaD bundles from a JSONL file, run verification and import, and optionally write JSONL output."""
    in_path = Path(input_path)
    if not in_path.is_file():
        raise DadImportError(f"DaD input JSONL file does not exist: {in_path}")

    bundles: List[Mapping[str, Any]] = []
    with in_path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                obj = json.loads(stripped)
            except Exception as exc:
                raise DadImportError(f"Invalid JSON at {in_path}:{line_no}: {exc}") from exc
            if not isinstance(obj, Mapping):
                raise DadImportError(f"Row at {in_path}:{line_no} must be a JSON object")
            bundles.append(obj)

    if not bundles:
        raise DadImportError(f"DaD input JSONL file contains no bundles: {in_path}")

    result = import_dad_bundles(
        bundles,
        config=config,
        contamination_filter=contamination_filter,
        strict=strict,
    )

    if output_path is not None:
        out_path = Path(output_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w", encoding="utf-8") as out_handle:
            for row in result.emitted_rows:
                out_handle.write(canonical_json(row) + "\n")

    return result
