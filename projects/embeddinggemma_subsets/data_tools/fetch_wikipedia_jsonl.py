#!/usr/bin/env python3
"""Fetch Wikipedia text and write JSONL files.

Modes:
- api: strict network control via MediaWiki API (recommended for capped downloads)
- hf:  Hugging Face datasets (may download large shard files before row caps apply)
"""

from __future__ import annotations

import argparse
import json
import random
import time
import urllib.parse
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


def _clean_text(s: str) -> str:
    return " ".join((s or "").split())


def _load_existing_api_state(path: Path) -> tuple[int, int, set[int]]:
    rows = 0
    written_bytes = 0
    seen_pageids: set[int] = set()
    if not path.exists():
        return rows, written_bytes, seen_pageids
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            if not line.strip():
                continue
            rows += 1
            written_bytes += len(line.encode("utf-8"))
            try:
                obj = json.loads(line)
                pid = int(obj.get("pageid", -1))
                if pid >= 0:
                    seen_pageids.add(pid)
            except Exception:
                continue
    return rows, written_bytes, seen_pageids


def _fetch_api_batch(lang: str, *, limit: int, timeout_s: float) -> list[dict[str, Any]]:
    base = f"https://{lang}.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "generator": "random",
        "grnnamespace": "0",
        "grnlimit": str(limit),
        "prop": "extracts",
        "explaintext": "1",
        "exsectionformat": "plain",
        "exlimit": "max",
        "redirects": "1",
    }
    url = f"{base}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "embeddinggemma-subsets-fetcher/1.0"},
    )
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:
        data = json.loads(resp.read().decode("utf-8", errors="replace"))
    pages = data.get("query", {}).get("pages", {})
    out: list[dict[str, Any]] = []
    for page in pages.values():
        title = str(page.get("title", "")).strip()
        extract = _clean_text(str(page.get("extract", "")))
        if not title or not extract:
            continue
        out.append({"title": title, "text": extract, "pageid": int(page.get("pageid", -1))})
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--langs", default="en,es,zh,ja,ar,fr,pt,hi")
    ap.add_argument("--mode", choices=["api", "hf"], default="api")
    ap.add_argument("--snapshot", default="20220301", help="Wikipedia snapshot prefix, e.g. 20220301")
    ap.add_argument("--dataset", default="wikimedia/wikipedia", help="HF dataset id (default: wikimedia/wikipedia)")
    ap.add_argument("--out-dir", default="/tmp/wiki_jsonl")
    ap.add_argument("--max-rows", type=int, default=64, help="Per-language row cap (default: 64). Set 0 for no cap.")
    ap.add_argument("--max-output-mb", type=int, default=0, help="Per-language output cap in MB (0 means no cap).")
    ap.add_argument("--max-requests", type=int, default=500, help="API mode: max HTTP requests per language.")
    ap.add_argument("--batch-pages", type=int, default=20, help="API mode: random pages per request (1-20).")
    ap.add_argument("--min-chars", type=int, default=200, help="Drop tiny extracts in API mode.")
    ap.add_argument("--sleep-ms", type=int, default=100, help="API mode: sleep between requests.")
    ap.add_argument("--timeout-s", type=float, default=20.0, help="API mode: request timeout seconds.")
    ap.add_argument("--retry-429-base-s", type=float, default=2.0, help="API mode: initial backoff on HTTP 429.")
    ap.add_argument("--retry-429-max-s", type=float, default=120.0, help="API mode: maximum backoff on HTTP 429.")
    ap.add_argument("--max-consecutive-errors", type=int, default=50, help="API mode: stop lang after too many consecutive errors.")
    args = ap.parse_args()

    langs = [x.strip() for x in str(args.langs).split(",") if x.strip()]
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for lang in langs:
        out_path = out_dir / f"{lang}.jsonl"
        cfg = f"{args.snapshot}.{lang}"
        n = 0
        written_bytes = 0
        max_bytes = int(args.max_output_mb) * 1024 * 1024 if int(args.max_output_mb) > 0 else 0
        seen_pageids: set[int] = set()
        req_count = 0
        consecutive_errors = 0
        backoff_s = float(args.retry_429_base_s)

        if args.mode == "hf":
            print(f"[{lang}] loading {args.dataset}/{cfg} ...")
            from datasets import load_dataset

            ds = load_dataset(args.dataset, cfg, split="train")
            # Resume-safe append behavior to avoid data loss on partial/failed reruns.
            mode = "a" if out_path.exists() else "w"
            if out_path.exists():
                with out_path.open("r", encoding="utf-8", errors="replace") as rf:
                    for line in rf:
                        if line.strip():
                            n += 1
                            written_bytes += len(line.encode("utf-8"))
            if int(args.max_rows) > 0 and n >= int(args.max_rows):
                print(f"[{lang}] resume skip: existing rows={n} >= max_rows={int(args.max_rows)}")
                continue
            if max_bytes > 0 and written_bytes >= max_bytes:
                print(f"[{lang}] resume skip: existing size={written_bytes/(1024*1024):.1f} MB >= max_output_mb={int(args.max_output_mb)}")
                continue
            with out_path.open(mode, encoding="utf-8") as f:
                for row in ds:
                    txt = _clean_text(str(row.get("text", "")))
                    if not txt:
                        continue
                    line = json.dumps({"text": txt}, ensure_ascii=False) + "\n"
                    line_bytes = len(line.encode("utf-8"))
                    if max_bytes > 0 and (written_bytes + line_bytes) > max_bytes:
                        break
                    f.write(line)
                    written_bytes += line_bytes
                    n += 1
                    if int(args.max_rows) > 0 and n >= int(args.max_rows):
                        break
            print(f"[{lang}] wrote {n} rows ({written_bytes/(1024*1024):.1f} MB) -> {out_path}")
            continue

        # API mode: resume-safe append + dedupe via pageid when available.
        n, written_bytes, seen_pageids = _load_existing_api_state(out_path)
        if int(args.max_rows) > 0 and n >= int(args.max_rows):
            print(f"[{lang}] resume skip: existing rows={n} >= max_rows={int(args.max_rows)}")
            continue
        if max_bytes > 0 and written_bytes >= max_bytes:
            print(f"[{lang}] resume skip: existing size={written_bytes/(1024*1024):.1f} MB >= max_output_mb={int(args.max_output_mb)}")
            continue

        print(
            f"[{lang}] api mode: max_requests={int(args.max_requests)} "
            f"batch_pages={int(args.batch_pages)} max_rows={int(args.max_rows)} "
            f"max_output_mb={int(args.max_output_mb)} existing_rows={n}"
        )
        with out_path.open("a", encoding="utf-8") as f:
            while True:
                if int(args.max_rows) > 0 and n >= int(args.max_rows):
                    break
                if max_bytes > 0 and written_bytes >= max_bytes:
                    break
                if req_count >= int(args.max_requests):
                    break

                req_count += 1
                try:
                    pages = _fetch_api_batch(
                        lang,
                        limit=max(1, min(20, int(args.batch_pages))),
                        timeout_s=float(args.timeout_s),
                    )
                    consecutive_errors = 0
                    backoff_s = float(args.retry_429_base_s)
                except Exception as e:
                    consecutive_errors += 1
                    if isinstance(e, urllib.error.HTTPError) and int(getattr(e, "code", 0)) == 429:
                        jitter = random.uniform(0.0, min(1.0, backoff_s * 0.2))
                        wait_s = min(float(args.retry_429_max_s), backoff_s + jitter)
                        print(f"[{lang}] request error #{req_count}: HTTP 429; sleeping {wait_s:.1f}s")
                        time.sleep(max(0.0, wait_s))
                        backoff_s = min(float(args.retry_429_max_s), max(0.5, backoff_s * 1.7))
                    else:
                        print(f"[{lang}] request error #{req_count}: {e}")
                        time.sleep(max(0.0, float(args.sleep_ms) / 1000.0))
                    if consecutive_errors >= int(args.max_consecutive_errors):
                        print(f"[{lang}] too many consecutive errors ({consecutive_errors}); stopping this language")
                        break
                    continue

                new_rows = 0
                hit_max_bytes = False
                for p in pages:
                    pid = int(p.get("pageid", -1))
                    if pid in seen_pageids:
                        continue
                    seen_pageids.add(pid)
                    txt = _clean_text(str(p.get("text", "")))
                    if len(txt) < int(args.min_chars):
                        continue
                    obj = {"text": txt, "title": str(p.get("title", "")), "pageid": pid}
                    line = json.dumps(obj, ensure_ascii=False) + "\n"
                    line_bytes = len(line.encode("utf-8"))
                    if max_bytes > 0 and (written_bytes + line_bytes) > max_bytes:
                        hit_max_bytes = True
                        break
                    f.write(line)
                    written_bytes += line_bytes
                    n += 1
                    new_rows += 1
                    if int(args.max_rows) > 0 and n >= int(args.max_rows):
                        break

                if hit_max_bytes:
                    break

                if req_count % 20 == 0:
                    print(
                        f"[{lang}] req={req_count} rows={n} "
                        f"mb={written_bytes/(1024*1024):.1f}"
                    )
                if new_rows == 0:
                    # avoid hot looping on low-yield responses
                    time.sleep(max(0.0, float(args.sleep_ms) / 1000.0))
                else:
                    time.sleep(max(0.0, float(args.sleep_ms) / 1000.0))

        print(
            f"[{lang}] wrote {n} rows ({written_bytes/(1024*1024):.1f} MB), "
            f"requests={req_count} -> {out_path}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
