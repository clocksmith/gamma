#!/usr/bin/env python3
"""
Evaluate base vs subset embedding models on per-language retrieval sets.

Outputs:
- metrics.json: retrieval metrics (Recall@K, MRR@K, nDCG@K), OOV rate, cosine stats
- charts/*.png: histograms + scatter plots (optional)

This uses the base tokenizer for both models. For the subset model, it remaps
token IDs using id_remap.json (old_id -> new_id) and falls back to unk.
"""

from __future__ import annotations

import argparse
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import numpy as np
except Exception:
    np = None  # type: ignore[assignment]


def _require_numpy() -> None:
    if np is None:
        raise SystemExit(
            "Missing dependency: numpy. Install project requirements "
            "(for example: `pip install -r requirements.txt`)."
        )


def _set_offline_env() -> None:
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")


def _set_mpl_env() -> None:
    # Avoid matplotlib trying to write to ~/.matplotlib (may be non-writable).
    os.environ.setdefault("MPLBACKEND", "Agg")
    os.environ.setdefault("MPLCONFIGDIR", "/tmp/mplconfig")
    # Fontconfig can also attempt to write caches under ~/.cache/fontconfig.
    os.environ.setdefault("XDG_CACHE_HOME", "/tmp/xdg-cache")
    os.environ.setdefault("FC_CACHEDIR", "/tmp/fontconfig")
    Path(os.environ["MPLCONFIGDIR"]).mkdir(parents=True, exist_ok=True)
    Path(os.environ["XDG_CACHE_HOME"]).mkdir(parents=True, exist_ok=True)
    Path(os.environ["FC_CACHEDIR"]).mkdir(parents=True, exist_ok=True)


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _load_dataset(dataset_path: Path) -> dict[str, Any]:
    """
    Supports:
    - single JSON file: { lang: {queries, docs, relevant}, ... }
    - dataset directory: datasets/<lang>/dataset.json
    """
    if dataset_path.is_dir():
        out: dict[str, Any] = {}
        for lang_dir in sorted([p for p in dataset_path.iterdir() if p.is_dir()]):
            ds_file = lang_dir / "dataset.json"
            if ds_file.exists():
                out[lang_dir.name] = _load_json(ds_file)
        if not out:
            raise RuntimeError(f"No datasets found under: {dataset_path} (expected <lang>/dataset.json)")
        return out

    obj = _load_json(dataset_path)
    if not isinstance(obj, dict):
        raise RuntimeError(f"Dataset file must be a dict keyed by language tags: {dataset_path}")
    return obj


def _validate_dataset_hardness(dataset: dict[str, Any], *, allow_non_hard: bool) -> None:
    if allow_non_hard:
        return
    bad: list[str] = []
    for lang, blob in dataset.items():
        if not isinstance(blob, dict):
            bad.append(str(lang))
            continue
        meta = blob.get("meta", {})
        difficulty = meta.get("difficulty") if isinstance(meta, dict) else None
        if str(difficulty).lower() != "hard":
            bad.append(str(lang))
    if bad:
        langs = ", ".join(sorted(bad))
        raise RuntimeError(
            f"Non-hard datasets detected for: {langs}. "
            "Regenerate with hard-mode generator or pass --allow-non-hard."
        )


def _softmax(x: np.ndarray) -> np.ndarray:
    x = x - np.max(x)
    ex = np.exp(x)
    s = ex.sum()
    if s <= 0:
        return np.ones_like(x) / float(len(x))
    return ex / s


def _kl(p: np.ndarray, q: np.ndarray) -> float:
    # KL(p||q), with epsilon smoothing.
    eps = 1e-12
    p = np.clip(p, eps, 1.0)
    q = np.clip(q, eps, 1.0)
    p = p / p.sum()
    q = q / q.sum()
    return float(np.sum(p * np.log(p / q)))


def _js(p: np.ndarray, q: np.ndarray) -> float:
    p = p / p.sum()
    q = q / q.sum()
    m = 0.5 * (p + q)
    return 0.5 * _kl(p, m) + 0.5 * _kl(q, m)


def _cosine_matrix(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    # a: [Q,H], b: [D,H] => [Q,D]
    a = a / np.clip(np.linalg.norm(a, axis=1, keepdims=True), 1e-12, None)
    b = b / np.clip(np.linalg.norm(b, axis=1, keepdims=True), 1e-12, None)
    return a @ b.T


def _recall_at_k(ranks: list[int], k: int) -> float:
    return float(np.mean([1.0 if r < k else 0.0 for r in ranks])) if ranks else 0.0


def _mrr_at_k(ranks: list[int], k: int) -> float:
    vals = []
    for r in ranks:
        if r < k:
            vals.append(1.0 / float(r + 1))
        else:
            vals.append(0.0)
    return float(np.mean(vals)) if vals else 0.0


def _ndcg_at_k(ranks: list[int], k: int) -> float:
    # Binary relevance, one relevant doc per query.
    vals = []
    for r in ranks:
        if r < k:
            dcg = 1.0 / np.log2(float(r + 2))
        else:
            dcg = 0.0
        idcg = 1.0  # relevant at rank 0
        vals.append(dcg / idcg)
    return float(np.mean(vals)) if vals else 0.0


@dataclass(frozen=True)
class LoadedModel:
    model: Any
    tokenizer: Any
    remap_old_to_new: dict[str, int] | None


def _load_models(
    base_model: str,
    subset_dir: str | None,
    device: str,
    *,
    base_tokenizer: str | None = None,
) -> tuple[LoadedModel, LoadedModel | None]:
    import torch
    from transformers import AutoModel, AutoTokenizer

    tok_src = str(base_tokenizer) if base_tokenizer else str(base_model)
    base_tok = AutoTokenizer.from_pretrained(tok_src, local_files_only=True, use_fast=True)
    base = AutoModel.from_pretrained(base_model, local_files_only=True, low_cpu_mem_usage=True).to(device)
    base.eval()
    base_remap: dict[str, int] | None = None
    base_path = Path(base_model)
    base_remap_path = base_path / "id_remap.json"
    if base_remap_path.exists():
        remap = _load_json(base_remap_path).get("old_to_new", {})
        if isinstance(remap, dict) and remap:
            base_remap = remap
    base_loaded = LoadedModel(model=base, tokenizer=base_tok, remap_old_to_new=base_remap)

    if not subset_dir:
        return base_loaded, None

    subset_path = Path(subset_dir)
    remap_path = subset_path / "id_remap.json"
    remap = _load_json(remap_path).get("old_to_new", {})
    if not isinstance(remap, dict) or not remap:
        raise RuntimeError(f"Invalid remap file: {remap_path}")

    subset = AutoModel.from_pretrained(str(subset_path), local_files_only=True, low_cpu_mem_usage=True).to(device)
    subset.eval()

    subset_loaded = LoadedModel(model=subset, tokenizer=base_tok, remap_old_to_new=remap)
    return base_loaded, subset_loaded


def _mean_pool(last_hidden, attention_mask):
    # torch tensors
    mask = attention_mask.unsqueeze(-1).to(dtype=last_hidden.dtype)
    summed = (last_hidden * mask).sum(dim=1)
    denom = mask.sum(dim=1).clamp_min(1.0)
    return summed / denom


def _prepare_batch(
    loaded: LoadedModel,
    texts: list[str],
    *,
    device: str,
    max_length: int,
) -> tuple[Any, Any, dict[str, float]]:
    import torch

    tok = loaded.tokenizer
    t0 = time.perf_counter()
    enc = tok(
        texts,
        return_tensors="pt",
        padding=True,
        truncation=True,
        max_length=max_length,
        add_special_tokens=True,
    )
    t1 = time.perf_counter()

    input_ids = enc["input_ids"]
    attention_mask = enc.get("attention_mask", None)
    if attention_mask is None:
        attention_mask = torch.ones_like(input_ids, dtype=torch.long)

    # Remap ids if needed. Track OOV rate for this batch.
    oov = 0
    total = int(input_ids.numel())
    t_remap0 = time.perf_counter()
    if loaded.remap_old_to_new is not None:
        remap = loaded.remap_old_to_new
        unk_old = tok.unk_token_id
        if unk_old is None:
            raise RuntimeError("Tokenizer has no unk_token_id; cannot remap for subset model.")
        unk_new = remap.get(str(int(unk_old)))
        if unk_new is None:
            raise RuntimeError("Remap missing unk mapping; ensure specials were kept.")

        ids = input_ids.cpu().tolist()
        for bi in range(len(ids)):
            row = ids[bi]
            new_row = []
            for t in row:
                key = str(int(t))
                nv = remap.get(key)
                if nv is None:
                    oov += 1
                    nv = int(unk_new)
                new_row.append(int(nv))
            ids[bi] = new_row
        input_ids = torch.tensor(ids, dtype=torch.long)
    t_remap1 = time.perf_counter()

    input_ids = input_ids.to(device)
    attention_mask = attention_mask.to(device)

    stats = {
        "encode_ms": float((t1 - t0) * 1000.0),
        "remap_ms": float((t_remap1 - t_remap0) * 1000.0),
        "oov_rate": float(oov / max(1, total)),
        "tokens": float(total),
        "texts": float(len(texts)),
    }
    return input_ids, attention_mask, stats


def _maybe_sync(device: str) -> None:
    if device.startswith("cuda"):
        try:
            import torch

            torch.cuda.synchronize()
        except Exception:
            return


def _forward_once(loaded: LoadedModel, input_ids, attention_mask) -> np.ndarray:
    import torch

    with torch.no_grad():
        out = loaded.model(input_ids=input_ids, attention_mask=attention_mask, return_dict=True)

    pooled = getattr(out, "pooler_output", None)
    if pooled is None:
        last_hidden = getattr(out, "last_hidden_state", None)
        if last_hidden is None:
            raise RuntimeError("Model output missing pooler_output and last_hidden_state.")
        pooled = _mean_pool(last_hidden, attention_mask)

    pooled = pooled.float()
    pooled = pooled / pooled.norm(p=2, dim=-1, keepdim=True).clamp_min(1e-12)
    return pooled.detach().cpu().numpy()


def _bench_forward(
    loaded: LoadedModel,
    input_ids,
    attention_mask,
    *,
    device: str,
    warmup: int,
    iters: int,
) -> dict[str, float]:
    if iters <= 0:
        return {}

    for _ in range(max(0, warmup)):
        _ = _forward_once(loaded, input_ids, attention_mask)
    _maybe_sync(device)

    times_ms: list[float] = []
    for _ in range(iters):
        _maybe_sync(device)
        t0 = time.perf_counter()
        _ = _forward_once(loaded, input_ids, attention_mask)
        _maybe_sync(device)
        t1 = time.perf_counter()
        times_ms.append((t1 - t0) * 1000.0)

    arr = np.array(times_ms, dtype=np.float64)
    return {
        "iters": float(iters),
        "warmup": float(warmup),
        "forward_ms_mean": float(arr.mean()),
        "forward_ms_p50": float(np.quantile(arr, 0.50)),
        "forward_ms_p95": float(np.quantile(arr, 0.95)),
    }


def _embed_texts(
    loaded: LoadedModel,
    texts: list[str],
    *,
    device: str,
    max_length: int,
    batch_size: int,
    bench_warmup: int,
    bench_iters: int,
) -> tuple[np.ndarray, dict[str, float]]:
    import torch

    if not texts:
        return np.zeros((0, 0), dtype=np.float32), {"texts": 0.0, "tokens": 0.0, "oov_rate": 0.0}

    wall_t0 = time.perf_counter()
    n = len(texts)
    bs = max(1, int(batch_size))
    chunks = [texts[i : i + bs] for i in range(0, n, bs)]

    all_vecs: list[np.ndarray] = []
    encode_ms = 0.0
    remap_ms = 0.0
    tokens = 0.0
    oov_tokens = 0.0
    bench: dict[str, float] = {}
    forward_ms: list[float] = []
    if device.startswith("cuda"):
        try:
            torch.cuda.reset_peak_memory_stats()
        except Exception:
            pass

    for ci, chunk in enumerate(chunks):
        input_ids, attention_mask, prep = _prepare_batch(loaded, chunk, device=device, max_length=max_length)
        encode_ms += float(prep.get("encode_ms", 0.0))
        remap_ms += float(prep.get("remap_ms", 0.0))
        tok_n = float(prep.get("tokens", 0.0))
        tokens += tok_n
        oov_tokens += float(prep.get("oov_rate", 0.0)) * tok_n

        if ci == 0:
            bench = _bench_forward(
                loaded,
                input_ids,
                attention_mask,
                device=device,
                warmup=bench_warmup,
                iters=bench_iters,
            )

        _maybe_sync(device)
        t0 = time.perf_counter()
        vec = _forward_once(loaded, input_ids, attention_mask)
        _maybe_sync(device)
        t1 = time.perf_counter()
        forward_ms.append(float((t1 - t0) * 1000.0))
        all_vecs.append(vec)

    vecs = np.concatenate(all_vecs, axis=0)
    wall_t1 = time.perf_counter()
    fwd_p50 = float(np.quantile(np.array(forward_ms, dtype=np.float64), 0.5)) if forward_ms else 0.0
    texts_per_s = (float(bs) / (fwd_p50 / 1000.0)) if fwd_p50 > 0 else 0.0
    prefill_ms = float(forward_ms[0]) if forward_ms else 0.0
    steady_ms = float(np.quantile(np.array(forward_ms[1:], dtype=np.float64), 0.5)) if len(forward_ms) > 1 else prefill_ms
    wall_ms = float((wall_t1 - wall_t0) * 1000.0)
    texts_per_s_total = (float(n) / (wall_ms / 1000.0)) if wall_ms > 0 else 0.0
    peak_alloc_mb = 0.0
    peak_reserved_mb = 0.0
    if device.startswith("cuda"):
        try:
            peak_alloc_mb = float(torch.cuda.max_memory_allocated() / (1024.0 * 1024.0))
            peak_reserved_mb = float(torch.cuda.max_memory_reserved() / (1024.0 * 1024.0))
        except Exception:
            peak_alloc_mb = 0.0
            peak_reserved_mb = 0.0
    stats = {
        "texts": float(n),
        "batch_size": float(bs),
        "batches": float(len(chunks)),
        "tokens": float(tokens),
        "oov_rate": float(oov_tokens / max(1.0, tokens)),
        "encode_ms": float(encode_ms),
        "remap_ms": float(remap_ms),
        "prefill_ms": prefill_ms,
        "steady_ms_p50": steady_ms,
        "forward_ms_p50_batch": float(fwd_p50),
        "texts_per_s_p50": float(texts_per_s),
        "wall_ms_total": wall_ms,
        "texts_per_s_total": float(texts_per_s_total),
        "peak_vram_allocated_mb": peak_alloc_mb,
        "peak_vram_reserved_mb": peak_reserved_mb,
    } | bench
    return vecs, stats


def _plot_hist(values: list[float], title: str, path: Path, *, bins: int = 60) -> None:
    _set_mpl_env()
    import matplotlib.pyplot as plt

    path.parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(8, 4.5))
    plt.hist(values, bins=bins, alpha=0.9)
    plt.title(title)
    plt.tight_layout()
    plt.savefig(path)
    plt.close()


def _plot_scatter(x: list[float], y: list[float], title: str, path: Path) -> None:
    _set_mpl_env()
    import matplotlib.pyplot as plt

    path.parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(5.5, 5.5))
    plt.scatter(x, y, s=10, alpha=0.5)
    plt.title(title)
    plt.xlabel("base")
    plt.ylabel("subset")
    plt.tight_layout()
    plt.savefig(path)
    plt.close()


def _rank_positions(scores: np.ndarray) -> np.ndarray:
    """
    Convert scores [D] into rank positions [D] where 0 is best (highest score).
    """
    order = np.argsort(-scores)
    pos = np.empty_like(order)
    pos[order] = np.arange(len(order))
    return pos


def _spearman_rho(a: np.ndarray, b: np.ndarray) -> float:
    # Pearson correlation on rank positions.
    a = a.astype(np.float64)
    b = b.astype(np.float64)
    a = a - a.mean()
    b = b - b.mean()
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    if denom <= 1e-12:
        return 0.0
    return float((a @ b) / denom)


def _jaccard(a: list[int], b: list[int]) -> float:
    sa = set(a)
    sb = set(b)
    u = sa | sb
    if not u:
        return 1.0
    return float(len(sa & sb) / len(u))


def _plot_bars(categories: list[str], series: dict[str, list[float]], title: str, path: Path, *, ylabel: str) -> None:
    _set_mpl_env()
    import matplotlib.pyplot as plt

    path.parent.mkdir(parents=True, exist_ok=True)
    x = np.arange(len(categories))
    n = max(1, len(series))
    width = 0.8 / n

    plt.figure(figsize=(max(8.0, 1.2 * len(categories)), 4.5))
    for i, (name, vals) in enumerate(series.items()):
        plt.bar(x + (i - (n - 1) / 2) * width, vals, width, label=name)

    plt.xticks(x, categories, rotation=25, ha="right")
    plt.title(title)
    plt.ylabel(ylabel)
    plt.legend()
    plt.tight_layout()
    plt.savefig(path)
    plt.close()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-model", default="google/embeddinggemma-300m", help="HF id or local path (must be cached).")
    ap.add_argument("--base-tokenizer", default=None, help="Optional tokenizer source for base/subset tokenization.")
    ap.add_argument("--subset-dir", default=None, help="Path to subset model dir (contains model.safetensors + id_remap.json).")
    ap.add_argument("--dataset", default=str(Path(__file__).resolve().parents[1] / "datasets"))
    ap.add_argument("--out", default=str(Path(__file__).resolve().parents[1] / "eval_output"))
    ap.add_argument("--langs", default=None, help="Comma-separated language tags to evaluate (default: all in dataset).")
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--max-length", type=int, default=128)
    ap.add_argument("--k", default="1,5,10", help="Comma-separated K values for Recall/MRR/nDCG.")
    ap.add_argument("--batch-size", type=int, default=64, help="Embedding batch size for docs/queries.")
    ap.add_argument("--allow-non-hard", action="store_true", help="Allow datasets without meta.difficulty=hard.")
    ap.add_argument("--charts", action="store_true", help="Write PNG charts into out/charts/")
    ap.add_argument("--bench-iters", type=int, default=25, help="Forward-only benchmark iterations per batch.")
    ap.add_argument("--bench-warmup", type=int, default=5, help="Forward-only warmup iterations per batch.")
    args = ap.parse_args()
    _require_numpy()

    _set_offline_env()

    dataset = _load_dataset(Path(args.dataset))
    _validate_dataset_hardness(dataset, allow_non_hard=bool(args.allow_non_hard))

    if args.langs:
        langs = [x.strip() for x in args.langs.split(",") if x.strip()]
    else:
        langs = list(dataset.keys())

    ks = [int(x.strip()) for x in str(args.k).split(",") if x.strip()]
    out_dir = Path(args.out)
    charts_dir = out_dir / "charts"

    base_loaded, subset_loaded = _load_models(
        args.base_model,
        args.subset_dir,
        args.device,
        base_tokenizer=args.base_tokenizer,
    )

    results: dict[str, Any] = {
        "base_model": args.base_model,
        "base_tokenizer": args.base_tokenizer,
        "subset_dir": args.subset_dir,
        "device": args.device,
        "max_length": int(args.max_length),
        "langs": langs,
        "k": ks,
        "bench_iters": int(args.bench_iters),
        "bench_warmup": int(args.bench_warmup),
        "per_lang": {},
    }

    # Warm up both models (small batch) to reduce timing noise.
    _ = _embed_texts(
        base_loaded,
        ["warmup"],
        device=args.device,
        max_length=min(16, args.max_length),
        batch_size=1,
        bench_warmup=0,
        bench_iters=0,
    )
    if subset_loaded is not None:
        _ = _embed_texts(
            subset_loaded,
            ["warmup"],
            device=args.device,
            max_length=min(16, args.max_length),
            batch_size=1,
            bench_warmup=0,
            bench_iters=0,
        )

    for lang in langs:
        blob = dataset.get(lang)
        if not isinstance(blob, dict):
            raise SystemExit(f"dataset[{lang}] must be an object")
        queries = blob.get("queries", [])
        docs = blob.get("docs", [])
        relevant = blob.get("relevant", [])
        if not isinstance(queries, list) or not isinstance(docs, list) or not isinstance(relevant, list):
            raise SystemExit(f"dataset[{lang}] must have queries/docs/relevant lists")

        # Embed docs once per model.
        base_doc_vecs, base_doc_stats = _embed_texts(
            base_loaded,
            docs,
            device=args.device,
            max_length=args.max_length,
            batch_size=int(args.batch_size),
            bench_warmup=int(args.bench_warmup),
            bench_iters=int(args.bench_iters),
        )
        base_q_vecs, base_q_stats = _embed_texts(
            base_loaded,
            queries,
            device=args.device,
            max_length=args.max_length,
            batch_size=int(args.batch_size),
            bench_warmup=int(args.bench_warmup),
            bench_iters=int(args.bench_iters),
        )

        subset_doc_vecs = None
        subset_q_vecs = None
        subset_doc_stats = None
        subset_q_stats = None
        if subset_loaded is not None:
            subset_doc_vecs, subset_doc_stats = _embed_texts(
                subset_loaded,
                docs,
                device=args.device,
                max_length=args.max_length,
                batch_size=int(args.batch_size),
                bench_warmup=int(args.bench_warmup),
                bench_iters=int(args.bench_iters),
            )
            subset_q_vecs, subset_q_stats = _embed_texts(
                subset_loaded,
                queries,
                device=args.device,
                max_length=args.max_length,
                batch_size=int(args.batch_size),
                bench_warmup=int(args.bench_warmup),
                bench_iters=int(args.bench_iters),
            )

        base_sims = _cosine_matrix(base_q_vecs, base_doc_vecs)  # [Q,D]
        if subset_loaded is not None:
            subset_sims = _cosine_matrix(subset_q_vecs, subset_doc_vecs)

        # Retrieval metrics.
        ranks_base: list[int] = []
        ranks_subset: list[int] = []
        kl_list: list[float] = []
        js_list: list[float] = []
        scatter_base: list[float] = []
        scatter_subset: list[float] = []
        top1_agree: list[float] = []
        spearman_list: list[float] = []
        topk_jaccard: dict[int, list[float]] = {k: [] for k in ks}

        # If a query has multiple relevant docs, we score best rank among them.
        rel_map: dict[int, list[int]] = {}
        for qi, di in relevant:
            rel_map.setdefault(int(qi), []).append(int(di))

        for qi in range(len(queries)):
            rel_docs = rel_map.get(qi, [])
            if not rel_docs:
                continue

            # Base rank.
            order = list(np.argsort(-base_sims[qi]))
            best_rank = min(order.index(di) for di in rel_docs)
            ranks_base.append(int(best_rank))

            if subset_loaded is not None:
                order_s = list(np.argsort(-subset_sims[qi]))
                best_rank_s = min(order_s.index(di) for di in rel_docs)
                ranks_subset.append(int(best_rank_s))

                # Compare distributions over docs for KL/JS.
                p = _softmax(base_sims[qi].astype(np.float64))
                q = _softmax(subset_sims[qi].astype(np.float64))
                kl_list.append(_kl(p, q))
                js_list.append(_js(p, q))

                # Scatter on relevant doc score (use first relevant doc id deterministically).
                di0 = int(rel_docs[0])
                scatter_base.append(float(base_sims[qi, di0]))
                scatter_subset.append(float(subset_sims[qi, di0]))

                # Agreement metrics (correctness vs base ranking behavior).
                top1_agree.append(1.0 if int(order[0]) == int(order_s[0]) else 0.0)
                base_pos = _rank_positions(base_sims[qi])
                sub_pos = _rank_positions(subset_sims[qi])
                spearman_list.append(_spearman_rho(base_pos, sub_pos))
                for k in ks:
                    kk = min(int(k), len(order))
                    topk_jaccard[k].append(_jaccard(order[:kk], order_s[:kk]))

        per_lang: dict[str, Any] = {
            "queries": int(len(queries)),
            "docs": int(len(docs)),
            "labeled_queries": int(len(ranks_base)),
            "base": {
                "timing": {"docs": base_doc_stats, "queries": base_q_stats},
                "retrieval": {
                    f"recall@{k}": _recall_at_k(ranks_base, k) for k in ks
                }
                | {f"mrr@{k}": _mrr_at_k(ranks_base, k) for k in ks}
                | {f"ndcg@{k}": _ndcg_at_k(ranks_base, k) for k in ks},
            },
        }

        if subset_loaded is not None:
            # Cosine consistency: base(text) vs subset(text). Do both docs and queries.
            cos_docs = np.sum(base_doc_vecs * subset_doc_vecs, axis=1).tolist()
            cos_q = np.sum(base_q_vecs * subset_q_vecs, axis=1).tolist()
            rank_shift = (np.array(ranks_subset, dtype=np.float64) - np.array(ranks_base, dtype=np.float64)).tolist() if ranks_base and ranks_subset else []
            rank_shift_abs = np.abs(np.array(rank_shift, dtype=np.float64)) if rank_shift else np.array([], dtype=np.float64)
            score_delta = (np.array(scatter_subset, dtype=np.float64) - np.array(scatter_base, dtype=np.float64)).tolist() if scatter_base and scatter_subset else []
            rs_hist_counts: list[int] = []
            rs_hist_edges: list[float] = []
            if rank_shift:
                h_counts, h_edges = np.histogram(np.array(rank_shift, dtype=np.float64), bins=41, range=(-200.0, 200.0))
                rs_hist_counts = [int(x) for x in h_counts.tolist()]
                rs_hist_edges = [float(x) for x in h_edges.tolist()]
            per_lang["subset"] = {
                "timing": {"docs": subset_doc_stats, "queries": subset_q_stats},
                "retrieval": {
                    f"recall@{k}": _recall_at_k(ranks_subset, k) for k in ks
                }
                | {f"mrr@{k}": _mrr_at_k(ranks_subset, k) for k in ks}
                | {f"ndcg@{k}": _ndcg_at_k(ranks_subset, k) for k in ks},
                "consistency": {
                    "cosine_docs": {
                        "mean": float(np.mean(cos_docs)) if cos_docs else 0.0,
                        "p05": float(np.quantile(cos_docs, 0.05)) if cos_docs else 0.0,
                        "p50": float(np.quantile(cos_docs, 0.50)) if cos_docs else 0.0,
                        "p95": float(np.quantile(cos_docs, 0.95)) if cos_docs else 0.0,
                    },
                    "cosine_queries": {
                        "mean": float(np.mean(cos_q)) if cos_q else 0.0,
                        "p05": float(np.quantile(cos_q, 0.05)) if cos_q else 0.0,
                        "p50": float(np.quantile(cos_q, 0.50)) if cos_q else 0.0,
                        "p95": float(np.quantile(cos_q, 0.95)) if cos_q else 0.0,
                    },
                },
                "divergence": {
                    "kl_mean": float(np.mean(kl_list)) if kl_list else 0.0,
                    "js_mean": float(np.mean(js_list)) if js_list else 0.0,
                },
                "agreement": {
                    "top1_agreement": float(np.mean(top1_agree)) if top1_agree else 0.0,
                    "spearman_mean": float(np.mean(spearman_list)) if spearman_list else 0.0,
                    "topk_jaccard_mean": {f"@{k}": float(np.mean(v)) if v else 0.0 for k, v in topk_jaccard.items()},
                },
                "distribution": {
                    "rank_shift_subset_minus_base": {
                        "mean": float(np.mean(rank_shift)) if rank_shift else 0.0,
                        "p50": float(np.quantile(rank_shift, 0.50)) if rank_shift else 0.0,
                        "p90": float(np.quantile(rank_shift, 0.90)) if rank_shift else 0.0,
                        "p99": float(np.quantile(rank_shift, 0.99)) if rank_shift else 0.0,
                        "abs_p90": float(np.quantile(rank_shift_abs, 0.90)) if rank_shift else 0.0,
                        "abs_p99": float(np.quantile(rank_shift_abs, 0.99)) if rank_shift else 0.0,
                        "hist_edges": rs_hist_edges,
                        "hist_counts": rs_hist_counts,
                    },
                    "relevant_score_delta_subset_minus_base": {
                        "mean": float(np.mean(score_delta)) if score_delta else 0.0,
                        "p05": float(np.quantile(score_delta, 0.05)) if score_delta else 0.0,
                        "p50": float(np.quantile(score_delta, 0.50)) if score_delta else 0.0,
                        "p95": float(np.quantile(score_delta, 0.95)) if score_delta else 0.0,
                    },
                },
            }

            if args.charts:
                _plot_hist(cos_docs, f"[{lang}] cosine(base(doc), subset(doc))", charts_dir / f"{lang}_cos_docs.png")
                _plot_hist(cos_q, f"[{lang}] cosine(base(q), subset(q))", charts_dir / f"{lang}_cos_queries.png")
                if kl_list:
                    _plot_hist(kl_list, f"[{lang}] KL(softmax(base_sims) || softmax(subset_sims))", charts_dir / f"{lang}_kl.png")
                if js_list:
                    _plot_hist(js_list, f"[{lang}] JS(softmax(base_sims), softmax(subset_sims))", charts_dir / f"{lang}_js.png")
                if scatter_base and scatter_subset:
                    _plot_scatter(scatter_base, scatter_subset, f"[{lang}] relevant score scatter", charts_dir / f"{lang}_relevant_scatter.png")

        results["per_lang"][lang] = per_lang

    _write_json(out_dir / "metrics.json", results)
    print(f"Wrote: {out_dir / 'metrics.json'}")
    if args.charts:
        print(f"Wrote charts: {charts_dir}")

        # Summary charts: "how each language performs vs base" at a glance.
        langs_sorted = [l for l in langs if l in results["per_lang"]]
        if subset_loaded is not None:
            recall1_base = []
            recall1_sub = []
            oov_q_sub = []
            spearman = []
            top1 = []
            cos_q_mean = []
            for l in langs_sorted:
                pl = results["per_lang"][l]
                recall1_base.append(float(pl["base"]["retrieval"].get("recall@1", 0.0)))
                recall1_sub.append(float(pl["subset"]["retrieval"].get("recall@1", 0.0)))
                oov_q_sub.append(float(pl["subset"]["timing"]["queries"].get("oov_rate", 0.0)))
                spearman.append(float(pl["subset"]["agreement"].get("spearman_mean", 0.0)))
                top1.append(float(pl["subset"]["agreement"].get("top1_agreement", 0.0)))
                cos_q_mean.append(float(pl["subset"]["consistency"]["cosine_queries"].get("mean", 0.0)))

            _plot_bars(
                langs_sorted,
                {"base_recall@1": recall1_base, "subset_recall@1": recall1_sub},
                "Retrieval: Recall@1 (base vs subset)",
                charts_dir / "summary_recall1.png",
                ylabel="Recall@1",
            )
            _plot_bars(
                langs_sorted,
                {"subset_oov_rate_queries": oov_q_sub},
                "Subset Health: OOV Rate (queries)",
                charts_dir / "summary_oov_rate.png",
                ylabel="OOV rate",
            )
            _plot_bars(
                langs_sorted,
                {"subset_cosine_queries_mean": cos_q_mean},
                "Consistency: cosine(base(q), subset(q)) mean",
                charts_dir / "summary_cosine_queries.png",
                ylabel="Cosine",
            )
            _plot_bars(
                langs_sorted,
                {"top1_agreement": top1, "spearman_mean": spearman},
                "Agreement With Base Rankings (higher is better)",
                charts_dir / "summary_agreement.png",
                ylabel="Score",
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
