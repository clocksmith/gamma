#!/usr/bin/env python3
"""
Evaluate TranslateGemma-style translation distill models on held-out triplets.

Supports:
- Teacher baseline comparison (optional).
- BLEU and chrF via `evaluate` package (if installed).
- Optional COMET score if `comet` is available and a checkpoint/model is provided.
"""

from __future__ import annotations

import argparse
import glob
import json
import statistics
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import torch

from transformers import AutoModelForCausalLM, AutoTokenizer

try:
    import evaluate
except Exception:  # pragma: no cover - optional
    evaluate = None

try:
    from comet import load_from_checkpoint
except Exception:  # pragma: no cover - optional
    load_from_checkpoint = None

try:
    from huggingface_hub import snapshot_download
except Exception:  # pragma: no cover - optional
    snapshot_download = None


_METRIC_CACHE: dict[str, Any] = {}
_COMET_MODEL_CACHE: dict[str, Any] = {}


@dataclass(frozen=True)
class EvalRow:
    source_lang: str
    target_lang: str
    source: str
    target_pos: str
    pair: str


@dataclass(frozen=True)
class VocabRemap:
    old_to_new: dict[int, int]
    new_to_old: list[int]
    unk_old: int
    unk_new: int

REQUIRED_TRANSLATE_PAIR_CANONICAL_KEYS = (
    "src_lang",
    "tgt_lang",
    "pair",
    "source",
    "target_pos",
    "target_neg",
)
REQUIRED_TRANSLATE_PAIR_COMPAT_KEYS = (
    "lang",
    "query",
    "pos",
    "neg",
)


def _safe_text(x: Any) -> str:
    if x is None:
        return ""
    return str(x).strip()


def _parse_csv_set(value: str) -> set[str]:
    return {x.strip() for x in str(value).split(",") if x.strip()}


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_jsonl_inputs(spec: str) -> list[Path]:
    raw = _safe_text(spec)
    if not raw:
        return []
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    if not parts:
        return []

    out: list[Path] = []
    seen: set[str] = set()
    for part in parts:
        matches: list[Path] = []
        if any(ch in part for ch in "*?["):
            matches = [Path(p) for p in sorted(glob.glob(part))]
        else:
            p = Path(part)
            if p.is_dir():
                matches = sorted(x for x in p.iterdir() if x.is_file() and x.suffix == ".jsonl")
            elif p.is_file():
                matches = [p]
            elif p.exists():
                raise RuntimeError(f"--pairs path is not a file or directory: {part}")
            else:
                raise RuntimeError(f"--pairs path does not exist: {part}")
        for m in matches:
            key = str(m.resolve())
            if key in seen:
                continue
            seen.add(key)
            out.append(m)
    if not out:
        raise RuntimeError(
            f"--pairs resolved to zero JSONL files from: {spec}. "
            "Provide a .jsonl file, a directory containing .jsonl shards, or a glob."
        )
    return out


def _load_vocab_remap(path: str, tokenizer) -> VocabRemap | None:
    if not str(path).strip():
        return None
    subset_dir = Path(path)
    if not subset_dir.exists():
        raise RuntimeError(f"vocab subset dir does not exist: {subset_dir}")
    remap_path = subset_dir / "id_remap.json"
    if not remap_path.exists():
        raise RuntimeError(f"missing id_remap.json in vocab subset dir: {remap_path}")
    remap_data = _load_json(remap_path)
    raw = remap_data.get("old_to_new", {})
    if not isinstance(raw, dict) or not raw:
        raise RuntimeError(f"invalid id_remap.json (old_to_new missing/empty): {remap_path}")

    old_to_new: dict[int, int] = {}
    for k, v in raw.items():
        try:
            old = int(k)
            new = int(v)
        except Exception:
            continue
        old_to_new[old] = new
    if not old_to_new:
        raise RuntimeError(f"could not parse old_to_new ids from: {remap_path}")

    new_to_old = remap_data.get("new_to_old")
    parsed_new_to_old: list[int] | None = None
    if isinstance(new_to_old, list):
        parsed: list[int] = []
        for x in new_to_old:
            try:
                parsed.append(int(x))
            except Exception:
                continue
        if parsed:
            parsed_new_to_old = parsed

    if parsed_new_to_old is None:
        size = max(old_to_new.values()) + 1
        rev: list[int] = [-1] * int(size)
        for old, new in old_to_new.items():
            if 0 <= int(new) < int(size):
                rev[int(new)] = int(old)
        parsed_new_to_old = [int(x) for x in rev if int(x) >= 0]

    if not parsed_new_to_old:
        raise RuntimeError(f"could not parse new_to_old from: {remap_path}")

    unk_old = tokenizer.unk_token_id
    if unk_old is None:
        raise RuntimeError(f"tokenizer has no unk_token_id; cannot load subset remap: {tokenizer}")
    unk_old = int(unk_old)
    unk_new = old_to_new.get(unk_old)
    if unk_new is None:
        raise RuntimeError(f"id_remap.json is missing unk mapping for token id {unk_old}: {remap_path}")
    return VocabRemap(
        old_to_new=old_to_new,
        new_to_old=parsed_new_to_old,
        unk_old=int(unk_old),
        unk_new=int(unk_new),
    )


def _remap_ids(input_ids: torch.Tensor, remap: VocabRemap) -> torch.Tensor:
    ids = input_ids.cpu().tolist()
    unk = int(remap.unk_new)
    remapped: list[list[int]] = []
    for row in ids:
        out: list[int] = []
        for value in row:
            try:
                token = int(value)
            except Exception:
                token = unk
            if token < 0:
                out.append(int(token))
            else:
                out.append(int(remap.old_to_new.get(token, unk)))
        remapped.append(out)
    return torch.tensor(remapped, dtype=torch.long, device=input_ids.device)


def _restore_ids_to_old_vocab(token_ids: torch.Tensor | int | list[int] | list[list[int]], remap: VocabRemap) -> torch.Tensor:
    if isinstance(token_ids, int):
        ids = [[int(token_ids)]]
    elif torch.is_tensor(token_ids):
        if token_ids.ndim == 0:
            ids = [[int(token_ids.item())]]
        elif token_ids.ndim == 1:
            ids = [token_ids.cpu().tolist()]
        else:
            ids = token_ids.cpu().tolist()
    elif isinstance(token_ids, tuple):
        if len(token_ids) == 0:
            ids = [[]]
        elif isinstance(token_ids[0], (list, tuple, torch.Tensor)):
            ids = [list(row.cpu().tolist() if torch.is_tensor(row) else list(row)) for row in token_ids]
        else:
            ids = [list(token_ids)]
    elif isinstance(token_ids, list):
        if len(token_ids) == 0:
            ids = [[]]
        elif isinstance(token_ids[0], (list, tuple, torch.Tensor)):
            ids = [list(row.cpu().tolist() if torch.is_tensor(row) else list(row)) for row in token_ids]
        else:
            ids = [list(token_ids)]
    else:
        ids = [[int(token_ids)]]
    unk_old = int(remap.unk_old)
    restored: list[list[int]] = []
    for row in ids:
        out: list[int] = []
        for value in row:
            try:
                token = int(value)
            except Exception:
                token = -1
            if token < 0 or token >= len(remap.new_to_old):
                out.append(int(unk_old))
            else:
                out.append(int(remap.new_to_old[token]))
        restored.append(out)
    return torch.tensor(restored, dtype=torch.long, device=token_ids.device if torch.is_tensor(token_ids) else "cpu")


def _parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--pairs",
        required=True,
        help=(
            "Translation triplets input: .jsonl file, directory of .jsonl shards, "
            "glob pattern, or comma-separated list of those."
        ),
    )
    ap.add_argument("--model", required=True, help="Student candidate model (HF model id/path or checkpoint path).")
    ap.add_argument(
        "--teacher-model",
        default="",
        help="Optional teacher model for baseline comparison.",
    )
    ap.add_argument(
        "--vocab-subset-dir",
        default="",
        help="Optional pruned-student directory containing id_remap.json (from tools/vocab_subset.py).",
    )
    ap.add_argument(
        "--tokenizer-model",
        default="",
        help=(
            "Optional tokenizer/model reference for subset-based student eval. "
            "Defaults to --teacher-model."
        ),
    )
    ap.add_argument(
        "--source-langs",
        default="",
        help='Optional comma-separated source language filter (empty=all).',
    )
    ap.add_argument(
        "--target-langs",
        default="",
        help='Optional comma-separated target language filter (example: "en,es").',
    )
    ap.add_argument("--out-dir", default="projects/distillation/translation/eval", help="Output directory.")
    ap.add_argument("--student-summary", default="", help="Optional student summary path (JSON).")
    ap.add_argument("--teacher-summary", default="", help="Optional teacher summary path (JSON).")
    ap.add_argument("--compare-summary", default="", help="Optional combined summary path (JSON).")
    ap.add_argument("--student-predictions", default="", help="Optional student predictions JSONL path.")
    ap.add_argument("--teacher-predictions", default="", help="Optional teacher predictions JSONL path.")
    ap.add_argument("--max-prompt-length", type=int, default=256)
    ap.add_argument("--max-new-tokens", type=int, default=192)
    ap.add_argument("--batch-size", type=int, default=2)
    ap.add_argument("--eval-samples", type=int, default=0, help="0 = all rows.")
    ap.add_argument("--device", default="auto")
    ap.add_argument("--dtype", default="auto", choices=["auto", "float16", "bfloat16", "float32"])
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--do-sample", action="store_true")
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--top-p", type=float, default=1.0)
    ap.add_argument("--top-k", type=int, default=50)
    ap.add_argument(
        "--allow-download",
        action="store_false",
        dest="local_files_only",
        default=True,
        help="Allow fetching missing models from network (default uses local cache only).",
    )
    ap.add_argument("--eval-bleu", action="store_true", help="Compute BLEU if available.")
    ap.add_argument("--eval-chrf", action="store_true", help="Compute chrF if available.")
    ap.add_argument("--eval-comet", action="store_true", help="Compute COMET if comet package is available.")
    ap.add_argument("--comet-model", default="Unbabel/wmt22-comet-da", help="COMET checkpoint id/path.")
    ap.add_argument("--comet-batch-size", type=int, default=8)
    ap.add_argument(
        "--allow-compat-mismatch",
        action="store_true",
        help="Allow source/query and target_pos/pos alias mismatches in eval JSONL.",
    )
    ap.add_argument(
        "--allow-partial-contract",
        action="store_true",
        help="Allow eval rows that omit compatibility alias keys (lang/query/pos/neg).",
    )
    return ap.parse_args()


def _choose_torch_dtype(dtype: str) -> torch.dtype:
    if dtype == "float16":
        return torch.float16
    if dtype == "bfloat16":
        return torch.bfloat16
    if dtype == "float32":
        return torch.float32
    if torch.cuda.is_available():
        return torch.bfloat16
    return torch.float32


def _resolve_device(device: str, fallback: str = "cpu") -> str:
    if device and device != "auto":
        return str(device)
    if torch.cuda.is_available():
        return "cuda"
    return fallback


def _contract_text(value: Any) -> str:
    return " ".join(_safe_text(value).split())


def _validate_pair_contract(
    obj: dict[str, Any],
    *,
    path: Path,
    line_no: int,
    allow_compat_mismatch: bool,
    allow_partial_contract: bool,
) -> None:
    required = REQUIRED_TRANSLATE_PAIR_CANONICAL_KEYS
    if not allow_partial_contract:
        required = REQUIRED_TRANSLATE_PAIR_CANONICAL_KEYS + REQUIRED_TRANSLATE_PAIR_COMPAT_KEYS
    missing = [k for k in required if k not in obj]
    if missing:
        raise RuntimeError(f"{path}:{line_no}: missing required keys: {missing}")

    src_lang = _contract_text(obj.get("src_lang") or obj.get("source_lang") or obj.get("src"))
    tgt_lang = _contract_text(obj.get("tgt_lang") or obj.get("target_lang") or obj.get("tgt"))
    pair = _contract_text(obj.get("pair"))
    source = _contract_text(obj.get("source"))
    target_pos = _contract_text(obj.get("target_pos") or obj.get("pos"))
    target_neg = _contract_text(obj.get("target_neg") or obj.get("neg"))
    if not src_lang or not tgt_lang or not source or not target_pos or not pair:
        raise RuntimeError(f"{path}:{line_no}: canonical translation fields contain empty values")
    expected_pair = f"{src_lang}-{tgt_lang}"
    if pair != expected_pair:
        raise RuntimeError(f"{path}:{line_no}: pair='{pair}' does not match src/tgt '{expected_pair}'")

    query = _contract_text(obj.get("query"))
    pos = _contract_text(obj.get("pos"))
    neg = _contract_text(obj.get("neg"))
    lang = _contract_text(obj.get("lang"))
    has_compat_alias = any(k in obj for k in REQUIRED_TRANSLATE_PAIR_COMPAT_KEYS)
    if has_compat_alias and not allow_compat_mismatch:
        if query and query != source:
            raise RuntimeError(f"{path}:{line_no}: source/query mismatch")
        if pos and pos != target_pos:
            raise RuntimeError(f"{path}:{line_no}: target_pos/pos mismatch")
        if target_neg and neg and neg != target_neg:
            raise RuntimeError(f"{path}:{line_no}: target_neg/neg mismatch")
        if lang and lang != tgt_lang:
            raise RuntimeError(f"{path}:{line_no}: lang='{lang}' does not match tgt_lang='{tgt_lang}'")


def _load_rows(
    paths: list[Path],
    source_langs: set[str],
    target_langs: set[str],
    max_rows: int,
    *,
    allow_compat_mismatch: bool,
    allow_partial_contract: bool,
) -> list[EvalRow]:
    rows: list[EvalRow] = []
    for path in paths:
        with path.open("r", encoding="utf-8") as f:
            for ln, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except Exception as exc:
                    raise RuntimeError(f"{path}:{ln}: invalid JSON row: {exc}") from exc
                if not isinstance(obj, dict):
                    raise RuntimeError(f"{path}:{ln}: expected JSON object row")
                _validate_pair_contract(
                    obj,
                    path=path,
                    line_no=ln,
                    allow_compat_mismatch=allow_compat_mismatch,
                    allow_partial_contract=allow_partial_contract,
                )
                source_lang = _safe_text(obj.get("src_lang") or obj.get("source_lang") or obj.get("src"))
                target_lang = _safe_text(obj.get("tgt_lang") or obj.get("target_lang") or obj.get("tgt"))
                source = _safe_text(obj.get("source"))
                target_pos = _safe_text(obj.get("target_pos") or obj.get("pos"))
                if source_langs and source_lang not in source_langs:
                    continue
                if target_langs and target_lang not in target_langs:
                    continue
                if not source or not target_pos or not source_lang or not target_lang:
                    continue
                pair = _safe_text(obj.get("pair")) or f"{source_lang}-{target_lang}"
                rows.append(
                    EvalRow(
                        source_lang=source_lang,
                        target_lang=target_lang,
                        source=source,
                        target_pos=target_pos,
                        pair=pair,
                    )
                )
                if max_rows > 0 and len(rows) >= max_rows:
                    return rows
    return rows


def _build_user_message(source_lang: str, target_lang: str, source_text: str, use_list_payload: bool) -> dict[str, Any]:
    item = {
        "type": "text",
        "source_lang_code": source_lang,
        "target_lang_code": target_lang,
        "text": source_text,
    }
    if use_list_payload:
        content = [item]
    else:
        content = json.dumps(item, ensure_ascii=False)
    return {"role": "user", "content": content}


def _to_chat_text(tokenizer, source_lang: str, target_lang: str, source_text: str) -> str:
    user_message = _build_user_message(source_lang, target_lang, source_text, use_list_payload=True)
    fallback = f"[{source_lang} -> {target_lang}] {source_text}"
    prompt_text = fallback
    use_list_payload = False
    try:
        has_chat_template = getattr(tokenizer, "chat_template", None) is not None
    except Exception:
        has_chat_template = False

    if has_chat_template and tokenizer is not None:
        try:
            prompt_text = tokenizer.apply_chat_template([user_message], tokenize=False, add_generation_prompt=True)
            use_list_payload = True
        except Exception:
            use_list_payload = False
    if not use_list_payload:
        user_message["content"] = json.dumps(user_message["content"], ensure_ascii=False)
        if has_chat_template and tokenizer is not None:
            try:
                prompt_text = tokenizer.apply_chat_template(
                    [user_message],
                    tokenize=False,
                    add_generation_prompt=True,
                )
            except Exception:
                prompt_text = fallback
        else:
            prompt_text = fallback
    return prompt_text


def _load_model_and_tokenizer(model_ref: str, device: str, dtype: torch.dtype, local_files_only: bool):
    tok = AutoTokenizer.from_pretrained(model_ref, local_files_only=local_files_only)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        model_ref,
        torch_dtype=dtype,
        local_files_only=local_files_only,
    )
    model.to(device)
    model.eval()
    return model, tok


def _generate_rows(
    model,
    tokenizer,
    vocab_remap: VocabRemap | None,
    rows: list[EvalRow],
    device: str,
    batch_size: int,
    max_prompt_length: int,
    max_new_tokens: int,
    do_sample: bool,
    temperature: float,
    top_p: float,
    top_k: int,
) -> list[str]:
    if not rows:
        return []
    out: list[str] = []
    for start in range(0, len(rows), max(1, batch_size)):
        chunk = rows[start : start + batch_size]
        prompts = [_to_chat_text(tokenizer, r.source_lang, r.target_lang, r.source) for r in chunk]
        batch_enc = tokenizer(
            prompts,
            return_tensors="pt",
            truncation=True,
            max_length=max_prompt_length,
            padding=True,
        )
        if vocab_remap is not None:
            batch_enc["input_ids"] = _remap_ids(batch_enc["input_ids"], vocab_remap)
        batch_enc = {k: v.to(device) for k, v in batch_enc.items()}
        gen_kwargs: dict[str, Any] = {
            "max_new_tokens": int(max_new_tokens),
            "do_sample": bool(do_sample),
            "top_p": float(top_p),
            "top_k": int(top_k),
            "pad_token_id": tokenizer.eos_token_id,
        }
        if do_sample:
            gen_kwargs["temperature"] = float(temperature)
        with torch.no_grad():
            generated = model.generate(
                input_ids=batch_enc["input_ids"],
                attention_mask=batch_enc["attention_mask"],
                **gen_kwargs,
            )
        prompt_lens = batch_enc["attention_mask"].sum(dim=1).tolist()
        for i in range(len(chunk)):
            p = int(prompt_lens[i])
            pred_ids = generated[i][p:]
            if vocab_remap is not None:
                pred_ids = _restore_ids_to_old_vocab(pred_ids, vocab_remap)
            if torch.is_tensor(pred_ids) and pred_ids.ndim > 1:
                pred_ids = pred_ids[0] if pred_ids.shape[0] > 0 else torch.tensor([], dtype=torch.long)
            pred = tokenizer.decode(pred_ids, skip_special_tokens=True)
            out.append(_safe_text(pred))
    return out


def _safe_metric_error(msg: str) -> dict[str, Any]:
    return {"available": False, "score": None, "error": msg}


def _normalize_metric_path(model_path: str) -> str | None:
    p = Path(model_path)
    if not p.exists():
        return None
    if p.is_file():
        return str(p)
    if not p.exists():
        return None
    if p.is_dir():
        for ckpt in sorted((p / "checkpoints").glob("*.ckpt")):
            if ckpt.is_file():
                return str(ckpt)
        if (p / "model.ckpt").is_file():
            return str(p / "model.ckpt")
        return str(p)
    return None


def _resolve_comet_checkpoint(path: str, allow_download: bool) -> tuple[str, str | None]:
    cached = _COMET_MODEL_CACHE.get(path)
    if isinstance(cached, str):
        return cached, None

    p = _normalize_metric_path(path)
    if p is not None:
        _COMET_MODEL_CACHE[path] = p
        return p, None

    # Remote Hugging Face style identifiers typically look like "org/repo".
    # Local filesystem paths are usually absolute or relative but point to an
    # existing file/dir, which we already handled above.
    if "/" not in path and not path.startswith(".") and not Path(path).is_absolute():
        return path, "comet model path does not exist and does not look like a Hugging Face repo id"

    if snapshot_download is None:
        return path, "huggingface_hub not installed for remote COMET id resolution"

    if not allow_download:
        return path, "comet model not found locally and --allow-download is disabled"

    try:
        local_snapshot = Path(snapshot_download(repo_id=path, local_files_only=False))
    except Exception as e:
        return path, f"failed to download COMET checkpoint {path}: {e}"

    resolved = _normalize_metric_path(str(local_snapshot))
    if resolved is None:
        return path, f"no checkpoint found in downloaded COMET artifact: {local_snapshot}"

    _COMET_MODEL_CACHE[path] = resolved
    return resolved, None

def _compute_metrics(predictions: list[str], references: list[str], do_bleu: bool, do_chrf: bool) -> dict[str, Any]:
    n = len(predictions)
    if not n:
        return {
            "n": 0,
            "bleu": _safe_metric_error("no data"),
            "chrf": _safe_metric_error("no data"),
        }
    out: dict[str, Any] = {
        "n": int(n),
        "exact_match": {
            "available": True,
            "score": 100.0 * sum(1 for p, t in zip(predictions, references) if _safe_text(p) == _safe_text(t)) / max(1, n),
        },
    }
    if do_bleu:
        if evaluate is None:
            out["bleu"] = _safe_metric_error("evaluate package unavailable")
        else:
            try:
                metric = _METRIC_CACHE.get("sacrebleu")
                if metric is None:
                    metric = evaluate.load("sacrebleu")
                    _METRIC_CACHE["sacrebleu"] = metric
                out["bleu"] = {
                    "available": True,
                    "score": float(metric.compute(predictions=predictions, references=[[r] for r in references])["score"]),
                }
            except Exception as e:
                out["bleu"] = _safe_metric_error(str(e))
    else:
        out["bleu"] = _safe_metric_error("disabled")

    if do_chrf:
        if evaluate is None:
            out["chrf"] = _safe_metric_error("evaluate package unavailable")
        else:
            try:
                metric = _METRIC_CACHE.get("chrf")
                if metric is None:
                    metric = evaluate.load("chrf")
                    _METRIC_CACHE["chrf"] = metric
                out["chrf"] = {
                    "available": True,
                    "score": float(metric.compute(predictions=predictions, references=references)["score"]),
                }
            except Exception as e:
                out["chrf"] = _safe_metric_error(str(e))
    else:
        out["chrf"] = _safe_metric_error("disabled")
    return out


def _compute_comet(
    rows: list[EvalRow],
    predictions: list[str],
    references: list[str],
    comet_model_path: str,
    batch_size: int,
    allow_download: bool,
) -> dict[str, Any]:
    if not predictions:
        return _safe_metric_error("no data")
    if load_from_checkpoint is None:
        return _safe_metric_error("comet package unavailable")
    try:
        resolved_model_path, model_error = _resolve_comet_checkpoint(
            comet_model_path,
            allow_download=allow_download,
        )
        if model_error:
            return _safe_metric_error(model_error)
        if resolved_model_path in _COMET_MODEL_CACHE:
            comet_model = _COMET_MODEL_CACHE[resolved_model_path]
        else:
            comet_model = load_from_checkpoint(resolved_model_path)
            _COMET_MODEL_CACHE[resolved_model_path] = comet_model
    except Exception as e:
        return _safe_metric_error(f"failed to load comet model: {e}")
    data = []
    for row, pred, ref in zip(rows, predictions, references):
        data.append({
            "src": row.source,
            "mt": pred,
            "ref": ref,
        })
    try:
        raw = comet_model.predict(
            data,
            batch_size=max(1, int(batch_size)),
            progress_bar=False,
            accelerator="cpu",
            gpus=0,
        )
        scores = [float(x) for x in raw.get("scores", [])]
        if not scores:
            return _safe_metric_error("comet model returned no scores")
        return {
            "available": True,
            "score": float(statistics.fmean(scores)),
            "count": int(len(scores)),
        }
    except Exception as e:
        return _safe_metric_error(f"comet inference failed: {e}")


def _evaluate_model(
    args: argparse.Namespace,
    model_ref: str,
    rows: list[EvalRow],
    out_dir: Path,
    pred_path: Path,
    summary_path: Path,
    label: str,
    vocab_subset_dir: str,
    tokenizer_ref: str,
    source_langs: set[str],
    target_langs: set[str],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    del source_langs, target_langs
    device = _resolve_device(str(args.device))
    dtype = _choose_torch_dtype(str(args.dtype))
    vocab_remap = None
    tokenizer = None
    if str(vocab_subset_dir).strip():
        base_tok_ref = str(tokenizer_ref).strip()
        if not base_tok_ref:
            base_tok_ref = model_ref
        tokenizer = AutoTokenizer.from_pretrained(base_tok_ref, local_files_only=bool(args.local_files_only))
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        vocab_remap = _load_vocab_remap(str(vocab_subset_dir), tokenizer)

    if tokenizer is None:
        model, tokenizer = _load_model_and_tokenizer(model_ref, device, dtype=dtype, local_files_only=bool(args.local_files_only))
    else:
        model = AutoModelForCausalLM.from_pretrained(
            model_ref,
            torch_dtype=dtype,
            local_files_only=bool(args.local_files_only),
        ).to(device)
        model.eval()

    rng = list(rows)
    if args.seed:
        # Deterministic output for deterministic decoding.
        torch.manual_seed(int(args.seed))

    pred_texts = _generate_rows(
        model=model,
        tokenizer=tokenizer,
        rows=rng,
        device=device,
        batch_size=int(args.batch_size),
        max_prompt_length=int(args.max_prompt_length),
        max_new_tokens=int(args.max_new_tokens),
        do_sample=bool(args.do_sample),
        temperature=float(args.temperature),
        top_p=float(args.top_p),
        top_k=int(args.top_k),
        vocab_remap=vocab_remap,
    )
    refs = [r.target_pos for r in rng]
    preds = [p for p in pred_texts]
    pred_rows: list[dict[str, Any]] = []
    for row, pred in zip(rng, preds):
        pred_rows.append(
            {
                "pair": row.pair,
                "src_lang": row.source_lang,
                "tgt_lang": row.target_lang,
                "source": row.source,
                "target_pos": row.target_pos,
                "pred": pred,
            }
        )
    out_dir.mkdir(parents=True, exist_ok=True)
    with pred_path.open("w", encoding="utf-8") as f:
        for rec in pred_rows:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    by_pair: dict[str, dict[str, list[str] | int]] = {}
    for row, pred in zip(rng, preds):
        by_pair.setdefault(row.pair, {"pred": [], "ref": []})
        by_pair[row.pair]["pred"].append(pred)
        by_pair[row.pair]["ref"].append(row.target_pos)

    pair_metrics: dict[str, Any] = {}
    for pair, bucket in by_pair.items():
        pred = list(bucket["pred"])  # type: ignore[list-item]
        ref = list(bucket["ref"])  # type: ignore[list-item]
        pair_metrics[pair] = _compute_metrics(pred, ref, args.eval_bleu, args.eval_chrf)
        if args.eval_comet and args.comet_model:
            pair_metrics[pair]["comet"] = _compute_comet(
                [r for r in rng if r.pair == pair],
                pred,
                ref,
                str(args.comet_model),
                int(args.comet_batch_size),
                allow_download=not bool(args.local_files_only),
            )

    overall = _compute_metrics(preds, refs, args.eval_bleu, args.eval_chrf)
    if args.eval_comet and args.comet_model:
        overall["comet"] = _compute_comet(
            rng,
            preds,
            refs,
            str(args.comet_model),
            int(args.comet_batch_size),
            allow_download=not bool(args.local_files_only),
        )

    summary = {
        "model": str(model_ref),
        "label": label,
        "count": int(len(rng)),
        "vocab_subset_dir": str(vocab_subset_dir),
        "vocab_subset_active": bool(vocab_remap is not None),
        "predictions": {
            "path": str(pred_path),
        },
        "metrics_overall": overall,
        "metrics_by_pair": pair_metrics,
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    # Free memory before loading next model.
    del model
    del tokenizer
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    return summary, pred_rows


def _write_summary(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _pair_delta(student_val: float | None, teacher_val: float | None) -> float | None:
    if student_val is None or teacher_val is None:
        return None
    return float(student_val) - float(teacher_val)


def main() -> int:
    args = _parse_args()
    torch.manual_seed(int(args.seed))
    source_langs = _parse_csv_set(str(args.source_langs))
    target_langs = _parse_csv_set(str(args.target_langs))
    pair_inputs = _resolve_jsonl_inputs(str(args.pairs))
    rows = _load_rows(
        pair_inputs,
        source_langs=source_langs,
        target_langs=target_langs,
        max_rows=int(args.eval_samples),
        allow_compat_mismatch=bool(args.allow_compat_mismatch),
        allow_partial_contract=bool(args.allow_partial_contract),
    )
    if not rows:
        raise RuntimeError("No evaluation rows after loading/filters.")

    out_root = Path(args.out_dir)
    if not args.student_summary:
        args.student_summary = str(out_root / "student_eval_summary.json")
    if not args.teacher_summary:
        args.teacher_summary = str(out_root / "teacher_eval_summary.json")
    if not args.compare_summary:
        args.compare_summary = str(out_root / "compare_eval_summary.json")
    if not args.student_predictions:
        args.student_predictions = str(out_root / "student_predictions.jsonl")
    if not args.teacher_predictions:
        args.teacher_predictions = str(out_root / "teacher_predictions.jsonl")

    student_tokenizer_ref = str(args.tokenizer_model).strip()
    if not student_tokenizer_ref:
        student_tokenizer_ref = str(args.teacher_model) if str(args.teacher_model).strip() else str(args.model)

    student_summary, student_preds = _evaluate_model(
        args=args,
        model_ref=str(args.model),
        rows=rows,
        out_dir=out_root,
        pred_path=Path(args.student_predictions),
        summary_path=Path(args.student_summary),
        label="student",
        vocab_subset_dir=str(args.vocab_subset_dir),
        tokenizer_ref=student_tokenizer_ref,
        source_langs=source_langs,
        target_langs=target_langs,
    )

    compare_out: dict[str, Any] = {
        "pairs": args.pairs,
        "pair_files": [str(p) for p in pair_inputs],
        "source_langs": sorted(source_langs),
        "target_langs": sorted(target_langs),
        "eval_samples": int(len(rows)),
        "vocab_subset_dir": str(args.vocab_subset_dir),
        "student": student_summary,
        "teacher": None,
        "delta": None,
    }

    if args.teacher_model:
        teacher_summary, _ = _evaluate_model(
            args=args,
            model_ref=str(args.teacher_model),
            rows=rows,
            out_dir=out_root,
            pred_path=Path(args.teacher_predictions),
            summary_path=Path(args.teacher_summary),
            label="teacher",
            vocab_subset_dir="",
            tokenizer_ref=str(args.teacher_model),
            source_langs=source_langs,
            target_langs=target_langs,
        )
        compare_out["teacher"] = teacher_summary

        student_overall = student_summary.get("metrics_overall", {})
        teacher_overall = teacher_summary.get("metrics_overall", {})
        delta: dict[str, Any] = {}
        for metric_key in ("bleu", "chrf", "comet"):
            s_metric = student_overall.get(metric_key, {})
            t_metric = teacher_overall.get(metric_key, {})
            if isinstance(s_metric, dict) and isinstance(t_metric, dict):
                s_score = s_metric.get("score")
                t_score = t_metric.get("score")
                delta[metric_key] = _pair_delta(s_score if isinstance(s_score, (int, float)) else None, t_score if isinstance(t_score, (int, float)) else None)
        compare_out["delta"] = delta

    _write_summary(Path(args.compare_summary), compare_out)
    print(f"[eval] wrote student summary: {args.student_summary}")
    if args.teacher_model:
        print(f"[eval] wrote teacher summary: {args.teacher_summary}")
    print(f"[eval] wrote compare summary: {args.compare_summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
