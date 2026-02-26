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


@dataclass(frozen=True)
class EvalRow:
    source_lang: str
    target_lang: str
    source: str
    target_pos: str
    pair: str


def _safe_text(x: Any) -> str:
    if x is None:
        return ""
    return str(x).strip()


def _parse_csv_set(value: str) -> set[str]:
    return {x.strip() for x in str(value).split(",") if x.strip()}


def _parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pairs", required=True, help="Translation triplets JSONL for evaluation.")
    ap.add_argument("--model", required=True, help="Student candidate model (HF model id/path or checkpoint path).")
    ap.add_argument(
        "--teacher-model",
        default="",
        help="Optional teacher model for baseline comparison.",
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


def _load_rows(path: Path, source_langs: set[str], target_langs: set[str], max_rows: int) -> list[EvalRow]:
    rows: list[EvalRow] = []
    with path.open("r", encoding="utf-8") as f:
        for ln, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            if not isinstance(obj, dict):
                continue
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
                break
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
            pred = tokenizer.decode(generated[i][p:], skip_special_tokens=True)
            out.append(_safe_text(pred))
    return out


def _safe_metric_error(msg: str) -> dict[str, Any]:
    return {"available": False, "score": None, "error": msg}


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
                metric = evaluate.load("sacrebleu")
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
                metric = evaluate.load("chrf")
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
) -> dict[str, Any]:
    if not predictions:
        return _safe_metric_error("no data")
    if load_from_checkpoint is None:
        return _safe_metric_error("comet package unavailable")
    try:
        comet_model = load_from_checkpoint(comet_model_path)
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
        raw = comet_model.predict(data, batch_size=max(1, int(batch_size)), progress_bar=False)
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
    source_langs: set[str],
    target_langs: set[str],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    del source_langs, target_langs
    device = _resolve_device(str(args.device))
    dtype = _choose_torch_dtype(str(args.dtype))
    model, tokenizer = _load_model_and_tokenizer(model_ref, device, dtype=dtype, local_files_only=bool(args.local_files_only))

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
            )

    overall = _compute_metrics(preds, refs, args.eval_bleu, args.eval_chrf)
    if args.eval_comet and args.comet_model:
        overall["comet"] = _compute_comet(rng, preds, refs, str(args.comet_model), int(args.comet_batch_size))

    summary = {
        "model": str(model_ref),
        "label": label,
        "count": int(len(rng)),
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
    rows = _load_rows(Path(args.pairs), source_langs=source_langs, target_langs=target_langs, max_rows=int(args.eval_samples))
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

    student_summary, student_preds = _evaluate_model(
        args=args,
        model_ref=str(args.model),
        rows=rows,
        out_dir=out_root,
        pred_path=Path(args.student_predictions),
        summary_path=Path(args.student_summary),
        label="student",
        source_langs=source_langs,
        target_langs=target_langs,
    )

    compare_out: dict[str, Any] = {
        "pairs": args.pairs,
        "source_langs": sorted(source_langs),
        "target_langs": sorted(target_langs),
        "eval_samples": int(len(rows)),
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
