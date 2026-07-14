#!/usr/bin/env python3
"""Run translation baseline evaluations for registered models.

Supports two explicit adapter paths:
  - causal-chat: instruction/chat causal models that translate through prompting
  - seq2seq: encoder-decoder translation models (MarianMT, NLLB, M2M100)

Emits standard compare_eval_summary.json artifacts compatible with the existing
distillation reporting pipeline (build_run_index.py, rebuild_translation_results_bundle.py).
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import statistics
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import yaml
except Exception:  # pragma: no cover
    yaml = None  # type: ignore[assignment]

try:
    import torch
except Exception:  # pragma: no cover
    torch = None  # type: ignore[assignment]

try:
    import sacrebleu
except Exception:  # pragma: no cover
    sacrebleu = None  # type: ignore[assignment]

try:
    from comet import load_from_checkpoint
except Exception:  # pragma: no cover
    load_from_checkpoint = None  # type: ignore[assignment]


BASELINES_YAML = Path(__file__).resolve().parents[1] / "baselines.yaml"
DEFAULT_RUNS_ROOT = Path(__file__).resolve().parents[1] / "runs"
REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from projects.distillation.translation.pipeline import run_stage_b_checkpoint_sweep as stage_b_sweep

# Language code mappings for seq2seq adapters.
NLLB_LANG_CODES = {"en": "eng_Latn", "es": "spa_Latn"}
M2M100_LANG_CODES = {"en": "en", "es": "es"}


@dataclass(frozen=True)
class EvalRow:
    source_lang: str
    target_lang: str
    source: str
    target_pos: str
    pair: str


@dataclass
class BaselineEntry:
    model_id: str
    display_name: str
    arch: str
    execution_mode: str
    prompt_adapter: str
    directions: list[str]
    license: str
    params: str
    revision: str
    tokenizer_id: str
    tokenizer_revision: str
    notes: str
    quality_tier: int
    enabled: bool

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BaselineEntry:
        return cls(
            model_id=str(data.get("model_id", "")),
            display_name=str(data.get("display_name", "")),
            arch=str(data.get("arch", "")),
            execution_mode=str(data.get("execution_mode", "")),
            prompt_adapter=str(data.get("prompt_adapter", "")),
            directions=list(data.get("directions", [])),
            license=str(data.get("license", "")),
            params=str(data.get("params", "")),
            revision=str(data.get("revision", "main")),
            tokenizer_id=str(data.get("tokenizer_id", "")),
            tokenizer_revision=str(data.get("tokenizer_revision", "main")),
            notes=str(data.get("notes", "")),
            quality_tier=int(data.get("quality_tier", 99)),
            enabled=bool(data.get("enabled", False)),
        )


@dataclass
class EvalResult:
    predictions: list[str]
    references: list[str]
    rows: list[EvalRow]
    metrics_overall: dict[str, Any] = field(default_factory=dict)
    metrics_by_pair: dict[str, Any] = field(default_factory=dict)
    direction_metrics: dict[str, Any] = field(default_factory=dict)


def _safe_text(x: Any) -> str:
    if x is None:
        return ""
    return str(x).strip()


def _model_slug(model_id: str) -> str:
    """Convert model ID to a safe directory name slug."""
    text = str(model_id or "").strip()
    text = text.replace("/", "__")
    text = re.sub(r"[^a-zA-Z0-9_.-]", "_", text)
    return text.lower()


def _now_utc() -> str:
    return dt.datetime.now(tz=dt.timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")


def _now_utc_display() -> str:
    return dt.datetime.now(tz=dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def _safe_metric(available: bool, score: float | None, **extra: Any) -> dict[str, Any]:
    out: dict[str, Any] = {"available": available, "score": score}
    out.update(extra)
    return out


def load_baselines(path: Path | None = None) -> list[BaselineEntry]:
    if path is None:
        path = BASELINES_YAML
    if yaml is None:
        raise RuntimeError("pyyaml is required: pip install pyyaml")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return [BaselineEntry.from_dict(entry) for entry in data.get("baselines", [])]


def load_eval_rows(
    paths: list[Path],
    directions: list[str] | None = None,
    max_rows: int = 0,
) -> list[EvalRow]:
    """Load evaluation rows from JSONL pair files."""
    rows: list[EvalRow] = []
    direction_set = set(directions) if directions else None
    for path in paths:
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                obj = json.loads(line)
                src_lang = _safe_text(obj.get("src_lang") or obj.get("source_lang"))
                tgt_lang = _safe_text(obj.get("tgt_lang") or obj.get("target_lang"))
                source = _safe_text(obj.get("source"))
                target_pos = _safe_text(obj.get("target_pos") or obj.get("pos"))
                pair = _safe_text(obj.get("pair")) or f"{src_lang}-{tgt_lang}"
                if not source or not target_pos or not src_lang or not tgt_lang:
                    continue
                if direction_set and pair not in direction_set:
                    continue
                rows.append(EvalRow(
                    source_lang=src_lang,
                    target_lang=tgt_lang,
                    source=source,
                    target_pos=target_pos,
                    pair=pair,
                ))
                if max_rows > 0 and len(rows) >= max_rows:
                    return rows
    return rows


# ---------------------------------------------------------------------------
# Causal-chat adapter
# ---------------------------------------------------------------------------

def _build_chat_prompt(tokenizer: Any, src_lang: str, tgt_lang: str, source_text: str) -> str:
    """Build chat prompt for causal translation models (TranslateGemma style)."""
    item = {
        "type": "text",
        "source_lang_code": src_lang,
        "target_lang_code": tgt_lang,
        "text": source_text,
    }
    user_message = {"role": "user", "content": [item]}
    fallback = f"[{src_lang} -> {tgt_lang}] {source_text}"

    has_chat_template = getattr(tokenizer, "chat_template", None) is not None
    if has_chat_template:
        try:
            return tokenizer.apply_chat_template(
                [user_message], tokenize=False, add_generation_prompt=True,
            )
        except Exception:
            pass
        # Try string content fallback.
        user_message["content"] = json.dumps(item, ensure_ascii=False)
        try:
            return tokenizer.apply_chat_template(
                [user_message], tokenize=False, add_generation_prompt=True,
            )
        except Exception:
            pass
    return fallback


def generate_causal_chat(
    model_id: str,
    rows: list[EvalRow],
    *,
    revision: str = "main",
    tokenizer_id: str = "",
    tokenizer_revision: str = "main",
    device: str = "auto",
    dtype: str = "auto",
    batch_size: int = 2,
    max_prompt_length: int = 256,
    max_new_tokens: int = 192,
    local_files_only: bool = True,
) -> list[str]:
    """Generate translations using a causal-chat model."""
    from transformers import AutoModelForCausalLM, AutoTokenizer

    resolved_device = _resolve_device(device)
    resolved_dtype = _resolve_dtype(dtype)

    tokenizer = AutoTokenizer.from_pretrained(
        tokenizer_id or model_id,
        revision=tokenizer_revision,
        local_files_only=local_files_only,
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        revision=revision,
        dtype=resolved_dtype,
        local_files_only=local_files_only,
    )
    model.to(resolved_device)
    model.eval()

    predictions: list[str] = []
    for start in range(0, len(rows), max(1, batch_size)):
        chunk = rows[start:start + batch_size]
        prompts = [_build_chat_prompt(tokenizer, r.source_lang, r.target_lang, r.source) for r in chunk]
        # add_special_tokens=False: chat template already adds <bos>; avoid double-BOS.
        batch_enc = tokenizer(
            prompts, return_tensors="pt", truncation=True,
            max_length=max_prompt_length, padding=True,
            add_special_tokens=False,
        )
        batch_enc = {k: v.to(resolved_device) for k, v in batch_enc.items()}
        with torch.no_grad():
            generated = model.generate(
                input_ids=batch_enc["input_ids"],
                attention_mask=batch_enc["attention_mask"],
                max_new_tokens=max_new_tokens,
                do_sample=False,
                top_p=1.0,
                top_k=50,
                pad_token_id=tokenizer.eos_token_id,
            )
        # Use padded input length, not attention_mask sum, for left-padded tokenizers.
        input_len = batch_enc["input_ids"].shape[1]
        for i in range(len(chunk)):
            pred_ids = generated[i][input_len:]
            pred = tokenizer.decode(pred_ids, skip_special_tokens=True)
            predictions.append(_safe_text(pred))

    del model
    del tokenizer
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    return predictions


# ---------------------------------------------------------------------------
# Seq2seq adapter
# ---------------------------------------------------------------------------

def _nllb_lang_code(lang: str) -> str:
    return NLLB_LANG_CODES.get(lang, lang)


def _m2m100_lang_code(lang: str) -> str:
    return M2M100_LANG_CODES.get(lang, lang)


def generate_seq2seq(
    model_id: str,
    rows: list[EvalRow],
    *,
    arch: str,
    revision: str = "main",
    tokenizer_id: str = "",
    tokenizer_revision: str = "main",
    device: str = "auto",
    dtype: str = "auto",
    batch_size: int = 8,
    max_length: int = 256,
    local_files_only: bool = True,
) -> list[str]:
    """Generate translations using a seq2seq model (MarianMT, NLLB, M2M100)."""
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

    resolved_device = _resolve_device(device)
    resolved_dtype = _resolve_dtype(dtype)

    tokenizer = AutoTokenizer.from_pretrained(
        tokenizer_id or model_id,
        revision=tokenizer_revision,
        local_files_only=local_files_only,
    )
    model = AutoModelForSeq2SeqLM.from_pretrained(
        model_id,
        revision=revision,
        dtype=resolved_dtype,
        local_files_only=local_files_only,
    )
    model.to(resolved_device)
    model.eval()

    # Group rows by direction for efficient batching with language tokens.
    direction_groups: dict[str, list[tuple[int, EvalRow]]] = {}
    for idx, row in enumerate(rows):
        direction_groups.setdefault(row.pair, []).append((idx, row))

    predictions: list[str | None] = [None] * len(rows)

    for pair, indexed_rows in direction_groups.items():
        src_lang = indexed_rows[0][1].source_lang
        tgt_lang = indexed_rows[0][1].target_lang

        # Configure tokenizer for this direction.
        forced_bos_token_id = None
        if arch == "nllb_seq2seq":
            tokenizer.src_lang = _nllb_lang_code(src_lang)
            tgt_code = _nllb_lang_code(tgt_lang)
            forced_bos_token_id = tokenizer.convert_tokens_to_ids(tgt_code)
        elif arch == "m2m100_seq2seq":
            tokenizer.src_lang = _m2m100_lang_code(src_lang)
            tgt_code = _m2m100_lang_code(tgt_lang)
            forced_bos_token_id = tokenizer.get_lang_id(tgt_code)
        # marian_seq2seq: no language tokens needed (bilingual model).

        for start in range(0, len(indexed_rows), max(1, batch_size)):
            chunk = indexed_rows[start:start + batch_size]
            sources = [row.source for _, row in chunk]
            batch_enc = tokenizer(
                sources, return_tensors="pt", truncation=True,
                max_length=max_length, padding=True,
            )
            batch_enc = {k: v.to(resolved_device) for k, v in batch_enc.items()}
            gen_kwargs: dict[str, Any] = {
                "max_new_tokens": max_length,
                "do_sample": False,
            }
            if forced_bos_token_id is not None:
                gen_kwargs["forced_bos_token_id"] = forced_bos_token_id
            with torch.no_grad():
                generated = model.generate(**batch_enc, **gen_kwargs)
            decoded = tokenizer.batch_decode(generated, skip_special_tokens=True)
            for i, (orig_idx, _) in enumerate(chunk):
                predictions[orig_idx] = _safe_text(decoded[i])

    del model
    del tokenizer
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    return [p or "" for p in predictions]


# ---------------------------------------------------------------------------
# Metric computation
# ---------------------------------------------------------------------------

def _resolve_device(device: str) -> str:
    if device and device != "auto":
        return device
    if torch is not None and torch.cuda.is_available():
        return "cuda"
    return "cpu"


def _resolve_dtype(dtype: str) -> Any:
    if torch is None:
        return None
    if dtype == "float16":
        return torch.float16
    if dtype == "bfloat16":
        return torch.bfloat16
    if dtype == "float32":
        return torch.float32
    if torch.cuda.is_available():
        return torch.bfloat16
    return torch.float32


def compute_metrics(
    predictions: list[str],
    references: list[str],
    *,
    do_bleu: bool = True,
    do_chrf: bool = True,
) -> dict[str, Any]:
    n = len(predictions)
    if not n:
        return {
            "n": 0,
            "exact_match": _safe_metric(False, None),
            "bleu": _safe_metric(False, None, error="no data"),
            "chrf": _safe_metric(False, None, error="no data"),
            "comet": _safe_metric(False, None, error="not computed"),
        }

    exact = 100.0 * sum(
        1 for p, r in zip(predictions, references) if _safe_text(p) == _safe_text(r)
    ) / max(1, n)
    out: dict[str, Any] = {
        "n": n,
        "exact_match": _safe_metric(True, exact),
    }

    if do_bleu and sacrebleu is not None:
        try:
            out["bleu"] = _safe_metric(True, float(sacrebleu.corpus_bleu(predictions, [references]).score))
        except Exception as e:
            out["bleu"] = _safe_metric(False, None, error=str(e))
    else:
        out["bleu"] = _safe_metric(False, None, error="sacrebleu unavailable" if not sacrebleu else "disabled")

    if do_chrf and sacrebleu is not None:
        try:
            chrf_metric = sacrebleu.metrics.CHRF()
            out["chrf"] = _safe_metric(True, float(chrf_metric.corpus_score(predictions, [references]).score))
        except Exception as e:
            out["chrf"] = _safe_metric(False, None, error=str(e))
    else:
        out["chrf"] = _safe_metric(False, None, error="sacrebleu unavailable" if not sacrebleu else "disabled")

    out["comet"] = _safe_metric(False, None, error="not computed for baseline")
    return out


def compute_direction_metrics(
    rows: list[EvalRow],
    predictions: list[str],
) -> dict[str, Any]:
    """Compute per-direction metrics and return normalized direction keys."""
    by_pair: dict[str, dict[str, list[str]]] = {}
    for row, pred in zip(rows, predictions):
        bucket = by_pair.setdefault(row.pair, {"pred": [], "ref": []})
        bucket["pred"].append(pred)
        bucket["ref"].append(row.target_pos)

    direction_metrics: dict[str, Any] = {}
    total_count = 0
    for pair, bucket in sorted(by_pair.items()):
        preds = bucket["pred"]
        refs = bucket["ref"]
        count = len(preds)
        total_count += count
        metrics = compute_metrics(preds, refs)
        # Normalize direction key: en-es -> en_es
        dir_key = pair.replace("-", "_")
        bleu_score = (metrics.get("bleu") or {}).get("score")
        chrf_score = (metrics.get("chrf") or {}).get("score")
        comet_score = (metrics.get("comet") or {}).get("score")
        direction_metrics[f"{dir_key}_bleu"] = bleu_score
        direction_metrics[f"{dir_key}_chrf"] = chrf_score
        direction_metrics[f"{dir_key}_comet"] = comet_score
        direction_metrics[f"{dir_key}_sample_count"] = count

    direction_metrics["total_sample_count"] = total_count
    return direction_metrics


def evaluate_model(
    baseline: BaselineEntry,
    rows: list[EvalRow],
    *,
    device: str = "auto",
    dtype: str = "auto",
    batch_size: int = 2,
    local_files_only: bool = True,
) -> EvalResult:
    """Evaluate a baseline model on a set of rows."""
    if torch is not None:
        torch.manual_seed(42)

    if baseline.execution_mode == "causal-chat":
        predictions = generate_causal_chat(
            baseline.model_id, rows,
            revision=baseline.revision,
            tokenizer_id=baseline.tokenizer_id,
            tokenizer_revision=baseline.tokenizer_revision,
            device=device, dtype=dtype, batch_size=batch_size,
            local_files_only=local_files_only,
        )
    elif baseline.execution_mode == "seq2seq":
        predictions = generate_seq2seq(
            baseline.model_id, rows,
            arch=baseline.arch,
            revision=baseline.revision,
            tokenizer_id=baseline.tokenizer_id,
            tokenizer_revision=baseline.tokenizer_revision,
            device=device, dtype=dtype,
            batch_size=batch_size, local_files_only=local_files_only,
        )
    else:
        raise ValueError(f"unsupported execution_mode: {baseline.execution_mode}")

    references = [r.target_pos for r in rows]
    overall = compute_metrics(predictions, references)

    # Per-pair metrics.
    by_pair: dict[str, dict[str, list[str]]] = {}
    for row, pred in zip(rows, predictions):
        bucket = by_pair.setdefault(row.pair, {"pred": [], "ref": []})
        bucket["pred"].append(pred)
        bucket["ref"].append(row.target_pos)
    pair_metrics = {}
    for pair, bucket in sorted(by_pair.items()):
        pair_metrics[pair] = compute_metrics(bucket["pred"], bucket["ref"])

    direction_metrics = compute_direction_metrics(rows, predictions)

    return EvalResult(
        predictions=predictions,
        references=references,
        rows=rows,
        metrics_overall=overall,
        metrics_by_pair=pair_metrics,
        direction_metrics=direction_metrics,
    )


# ---------------------------------------------------------------------------
# Artifact emission
# ---------------------------------------------------------------------------

def _build_model_summary(
    baseline: BaselineEntry,
    result: EvalResult,
    pred_path: Path,
) -> dict[str, Any]:
    return {
        "model": baseline.model_id,
        "label": "student",
        "count": len(result.rows),
        "vocab_subset_dir": "",
        "vocab_subset_active": False,
        "predictions": {"path": str(pred_path)},
        "metrics_overall": result.metrics_overall,
        "metrics_by_pair": result.metrics_by_pair,
    }


def _build_compare_summary(
    baseline: BaselineEntry,
    result: EvalResult,
    *,
    pairs_spec: str,
    pair_files: list[str],
    pred_path: Path,
    device: str,
    dtype: str,
) -> dict[str, Any]:
    source_langs = sorted({r.source_lang for r in result.rows})
    target_langs = sorted({r.target_lang for r in result.rows})

    comet_overall = result.metrics_overall.get("comet", {})
    comet_available = bool(comet_overall.get("available", False))

    return {
        "pairs": pairs_spec,
        "pair_files": pair_files,
        "source_langs": source_langs,
        "target_langs": target_langs,
        "eval_samples": len(result.rows),
        "vocab_subset_dir": "",
        "student": _build_model_summary(baseline, result, pred_path),
        "teacher": None,
        "delta": None,
        "direction_metrics": result.direction_metrics,
        "decode_metadata": {
            "decode_mode": "greedy",
            "temperature": 0.0,
            "top_p": 1.0,
            "top_k": 50,
        },
        "provenance": {
            "model_id": baseline.model_id,
            "model_revision": baseline.revision,
            "tokenizer_id": baseline.tokenizer_id,
            "tokenizer_revision": baseline.tokenizer_revision,
            "eval_dataset_path": pairs_spec,
            "eval_dataset_label": "",
            "adapter_name": baseline.prompt_adapter,
            "runtime_device": _resolve_device(device),
            "dtype": dtype if dtype != "auto" else ("bfloat16" if torch and torch.cuda.is_available() else "float32"),
            "execution_mode": baseline.execution_mode,
            "arch": baseline.arch,
            "comet_available": comet_available,
        },
        "baseline_metadata": {
            "is_baseline": True,
            "display_name": baseline.display_name,
            "quality_tier": baseline.quality_tier,
            "params": baseline.params,
            "license": baseline.license,
            "directions": baseline.directions,
        },
    }


def write_baseline_artifacts(
    out_root: Path,
    eval_name: str,
    baseline: BaselineEntry,
    result: EvalResult,
    *,
    pairs_spec: str,
    pair_files: list[str],
    decode: str = "greedy",
    device: str = "auto",
    dtype: str = "auto",
    duration_s: float = 0.0,
) -> Path:
    """Write standard evaluation artifacts for a baseline eval run."""
    eval_dir_name = f"{eval_name}__final__{decode}"
    eval_dir = out_root / eval_dir_name
    eval_dir.mkdir(parents=True, exist_ok=True)

    # Write predictions.
    pred_path = eval_dir / "student_predictions.jsonl"
    with pred_path.open("w", encoding="utf-8") as f:
        for row, pred in zip(result.rows, result.predictions):
            f.write(json.dumps({
                "pair": row.pair,
                "src_lang": row.source_lang,
                "tgt_lang": row.target_lang,
                "source": row.source,
                "target_pos": row.target_pos,
                "pred": pred,
            }, ensure_ascii=False) + "\n")

    # Write student eval summary.
    student_summary = _build_model_summary(baseline, result, pred_path)
    student_summary_path = eval_dir / "student_eval_summary.json"
    student_summary_path.write_text(
        json.dumps(student_summary, indent=2, sort_keys=True) + "\n", encoding="utf-8",
    )

    # Write compare eval summary.
    compare_summary = _build_compare_summary(
        baseline, result,
        pairs_spec=pairs_spec, pair_files=pair_files,
        pred_path=pred_path, device=device, dtype=dtype,
    )
    compare_path = eval_dir / "compare_eval_summary.json"
    compare_path.write_text(
        json.dumps(compare_summary, indent=2, sort_keys=True) + "\n", encoding="utf-8",
    )

    return eval_dir


def append_sweep_manifest_row(
    manifest_path: Path,
    *,
    run_dir: Path,
    eval_dir: Path,
    eval_name: str,
    eval_pairs: Path,
    result: EvalResult,
    duration_s: float,
    device: str,
    decode: str,
) -> None:
    bleu = (result.metrics_overall.get("bleu") or {}).get("score")
    chrf = (result.metrics_overall.get("chrf") or {}).get("score")
    row = {
        "checkpoint_name": "final",
        "checkpoint_step": 0,
        "checkpoint_path": "",
        "compare_summary": str(eval_dir / "compare_eval_summary.json"),
        "decode": decode,
        "duration_s": duration_s,
        "eval_name": eval_name,
        "log_path": "",
        "out_dir": str(eval_dir),
        "pairs": str(eval_pairs),
        "run_root": str(run_dir),
        "runtime_device": _resolve_device(device),
        "samples": len(result.rows),
        "status": 0,
        "student_predictions": str(eval_dir / "student_predictions.jsonl"),
        "timestamp_utc": _now_utc_display(),
        "bleu": bleu,
        "chrf": chrf,
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with manifest_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=True) + "\n")


def write_baseline_manifest(
    run_dir: Path,
    baseline: BaselineEntry,
    *,
    eval_dataset_paths: list[str],
    timestamp: float,
    device: str,
    dtype: str,
) -> Path:
    """Write baseline_manifest.json for run discovery."""
    manifest = {
        "baseline": True,
        "model_id": baseline.model_id,
        "display_name": baseline.display_name,
        "arch": baseline.arch,
        "execution_mode": baseline.execution_mode,
        "prompt_adapter": baseline.prompt_adapter,
        "directions": baseline.directions,
        "params": baseline.params,
        "license": baseline.license,
        "revision": baseline.revision,
        "tokenizer_id": baseline.tokenizer_id,
        "tokenizer_revision": baseline.tokenizer_revision,
        "quality_tier": baseline.quality_tier,
        "timestamp": timestamp,
        "eval_dataset_paths": eval_dataset_paths,
        "source_langs": sorted({d.split("-")[0] for d in baseline.directions}),
        "target_langs": sorted({d.split("-")[1] for d in baseline.directions}),
        "runtime_device": _resolve_device(device),
        "dtype": dtype,
    }
    manifest_path = run_dir / "baseline_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8",
    )
    return manifest_path


def write_run_contract(
    run_dir: Path,
    baseline: BaselineEntry,
    *,
    eval_dataset_paths: list[str],
    device: str,
) -> Path:
    """Write run_contract.txt for compatibility with existing run discovery."""
    contract = (
        f"[run-contract] run_name={run_dir.name} "
        f"pairs_input_spec=baseline "
        f"resume_from=none resume_stage=none "
        f"decode=greedy "
        f"eval_dataset_paths={','.join(eval_dataset_paths)} "
        f"device={_resolve_device(device)} "
        f"schedule=baseline "
        f"runtime_mode=baseline "
        f"model_id={baseline.model_id} "
        f"model_revision={baseline.revision} "
        f"tokenizer_id={baseline.tokenizer_id} "
        f"tokenizer_revision={baseline.tokenizer_revision} "
        f"execution_mode={baseline.execution_mode} "
        f"arch={baseline.arch}"
    )
    contract_path = run_dir / "run_contract.txt"
    contract_path.write_text(contract + "\n", encoding="utf-8")
    return contract_path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

EVAL_DATASET_SPECS: dict[str, str] = {
    "eval2_external": "projects/distillation/translation/training_data/translate_distill_pairs.eval2_wmt13_enes_128.jsonl",
    "eval3_indomain_clean": "projects/distillation/translation/training_data/translate_distill_pairs.eval3_indomain_clean_merged_128.jsonl",
}


def _parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Run translation baseline evaluations.")
    ap.add_argument(
        "--baseline",
        default="",
        help="Baseline model_id or display_name from baselines.yaml.",
    )
    ap.add_argument(
        "--all-enabled",
        action="store_true",
        help="Run all enabled baselines from the registry.",
    )
    ap.add_argument(
        "--baselines-yaml",
        default=str(BASELINES_YAML),
        help="Path to baselines.yaml registry.",
    )
    ap.add_argument(
        "--eval-datasets",
        default="eval2_external,eval3_indomain_clean",
        help="Comma-separated eval dataset names.",
    )
    ap.add_argument(
        "--runs-root",
        default=str(DEFAULT_RUNS_ROOT),
        help="Root directory for run output.",
    )
    ap.add_argument("--device", default="auto")
    ap.add_argument("--dtype", default="auto", choices=["auto", "float16", "bfloat16", "float32"])
    ap.add_argument("--batch-size", type=int, default=2)
    ap.add_argument("--eval-samples", type=int, default=0, help="0 = all rows.")
    ap.add_argument(
        "--allow-download",
        action="store_false",
        dest="local_files_only",
        default=True,
        help="Allow fetching missing models from network.",
    )
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--dry-run", action="store_true", help="Print plan without executing.")
    return ap.parse_args()


def _find_baseline(entries: list[BaselineEntry], name: str) -> BaselineEntry | None:
    for entry in entries:
        if entry.model_id == name or entry.display_name == name:
            return entry
    # Fuzzy match on slug.
    slug = _model_slug(name)
    for entry in entries:
        if _model_slug(entry.model_id) == slug or _model_slug(entry.display_name) == slug:
            return entry
    return None


def run_baseline_eval(
    baseline: BaselineEntry,
    eval_datasets: list[tuple[str, Path]],
    *,
    runs_root: Path,
    device: str = "auto",
    dtype: str = "auto",
    batch_size: int = 2,
    eval_samples: int = 0,
    local_files_only: bool = True,
    seed: int = 42,
) -> Path:
    """Run a full baseline evaluation and emit artifacts."""
    timestamp = time.time()
    timestamp_str = _now_utc()
    slug = _model_slug(baseline.model_id)
    run_name = f"baseline__{slug}__{timestamp_str}"
    run_dir = runs_root / run_name
    run_dir.mkdir(parents=True, exist_ok=True)
    sweep_dir = run_dir / "baseline_checkpoint_sweep_greedy"
    manifest_path = sweep_dir / "manifest.jsonl"

    eval_dataset_paths = [str(p) for _, p in eval_datasets]
    write_run_contract(run_dir, baseline, eval_dataset_paths=eval_dataset_paths, device=device)

    print(f"[baseline] model={baseline.model_id}")
    print(f"[baseline] model_revision={baseline.revision}")
    print(f"[baseline] tokenizer={baseline.tokenizer_id}@{baseline.tokenizer_revision}")
    print(f"[baseline] arch={baseline.arch} execution_mode={baseline.execution_mode}")
    print(f"[baseline] run_dir={run_dir}")

    for eval_name, eval_path in eval_datasets:
        print(f"[baseline] evaluating: {eval_name} ({eval_path})")
        rows = load_eval_rows(
            [eval_path],
            directions=baseline.directions,
            max_rows=eval_samples,
        )
        if not rows:
            print(f"[baseline] WARNING: no rows for {eval_name} with directions={baseline.directions}")
            continue

        t0 = time.time()
        result = evaluate_model(
            baseline, rows,
            device=device, dtype=dtype, batch_size=batch_size,
            local_files_only=local_files_only,
        )
        duration = time.time() - t0

        eval_dir = write_baseline_artifacts(
            sweep_dir, eval_name, baseline, result,
            pairs_spec=str(eval_path),
            pair_files=[str(eval_path)],
            device=device, dtype=dtype, duration_s=duration,
        )
        append_sweep_manifest_row(
            manifest_path,
            run_dir=run_dir,
            eval_dir=eval_dir,
            eval_name=eval_name,
            eval_pairs=eval_path,
            result=result,
            duration_s=duration,
            device=device,
            decode="greedy",
        )

        bleu = (result.metrics_overall.get("bleu") or {}).get("score")
        chrf = (result.metrics_overall.get("chrf") or {}).get("score")
        print(f"[baseline] {eval_name}: BLEU={bleu:.4f} chrF={chrf:.4f} ({len(rows)} samples, {duration:.1f}s)")

    write_baseline_manifest(
        run_dir, baseline,
        eval_dataset_paths=eval_dataset_paths,
        timestamp=timestamp,
        device=device, dtype=dtype,
    )
    manifest_rows = stage_b_sweep._read_manifest(manifest_path)
    stage_b_sweep._write_scoreboard(
        sweep_dir,
        manifest_rows,
        REPO_ROOT,
        run_dir,
        "greedy",
        eval_datasets,
    )

    print(f"[baseline] done: {run_dir}")
    return run_dir


def main() -> int:
    args = _parse_args()

    if torch is not None and args.seed:
        torch.manual_seed(args.seed)

    baselines = load_baselines(Path(args.baselines_yaml))
    runs_root = Path(args.runs_root)
    repo_root = REPO_ROOT

    # Resolve eval datasets.
    eval_names = [name.strip() for name in str(args.eval_datasets).split(",") if name.strip()]
    eval_datasets: list[tuple[str, Path]] = []
    for name in eval_names:
        rel_path = EVAL_DATASET_SPECS.get(name, name)
        full_path = repo_root / rel_path if not Path(rel_path).is_absolute() else Path(rel_path)
        if not full_path.is_file():
            print(f"[baseline] WARNING: eval dataset not found: {full_path}")
            continue
        eval_datasets.append((name, full_path))
    if not eval_datasets:
        print("[baseline] ERROR: no eval datasets found")
        return 1

    # Select baselines to run.
    targets: list[BaselineEntry] = []
    if args.all_enabled:
        targets = [b for b in baselines if b.enabled]
    elif args.baseline:
        entry = _find_baseline(baselines, args.baseline)
        if entry is None:
            print(f"[baseline] ERROR: baseline not found: {args.baseline}")
            print(f"[baseline] available: {[b.model_id for b in baselines]}")
            return 1
        targets = [entry]
    else:
        print("[baseline] ERROR: specify --baseline <name> or --all-enabled")
        return 1

    if not targets:
        print("[baseline] no baselines to run")
        return 0

    if args.dry_run:
        print("[baseline] DRY RUN - would evaluate:")
        for b in targets:
            print(f"  {b.model_id}@{b.revision} ({b.execution_mode}/{b.arch})")
            for name, path in eval_datasets:
                print(f"    -> {name}: {path}")
        return 0

    failures = 0
    for baseline in targets:
        try:
            run_baseline_eval(
                baseline, eval_datasets,
                runs_root=runs_root,
                device=args.device,
                dtype=args.dtype,
                batch_size=args.batch_size,
                eval_samples=args.eval_samples,
                local_files_only=args.local_files_only,
                seed=args.seed,
            )
        except Exception as exc:
            print(f"[baseline] ERROR evaluating {baseline.model_id}: {exc}")
            import traceback
            traceback.print_exc()
            failures += 1

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
