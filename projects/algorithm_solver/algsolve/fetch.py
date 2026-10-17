"""Fetch the approved, bounded source files and record a hash manifest.

Only the files named in SOURCES are fetched. Every file is pinned to a
revision, hashed, and written under data/raw/. The model snapshot goes to the
Hugging Face cache (HF_HOME) and is recorded by revision and file list.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

LANE_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = LANE_ROOT / "data" / "raw"
MANIFEST_PATH = RAW_DIR / "fetch_manifest.json"

DOOCS_REPO = "doocs/leetcode"
DOOCS_COMMIT = "88c8c2c29f19c186d7cc05c9db17245d9ae3df43"
MODEL_REPO = "Qwen/Qwen3.5-4B"

HF_DATASET_FILES = (
    {
        "repo": "newfacade/LeetCodeDataset",
        "files": ("LeetCodeDataset-train.jsonl", "LeetCodeDataset-test.jsonl"),
        "license": "apache-2.0 (HF card) / MIT (GitHub); conflict recorded",
    },
    {
        "repo": "livecodebench/code_generation_lite",
        "files": ("test6.jsonl",),
        "license": "card 'cc' / loader 'MIT'; conflict recorded",
    },
    {
        "repo": "open-r1/codeforces",
        "files": ("verifiable/test-00000-of-00001.parquet",),
        "license": "cc-by-4.0 (YAML) / ODC-By 4.0 (card); conflict recorded",
    },
    {
        "repo": "open-r1/codeforces-submissions",
        "files": ("selected_accepted/train-00000-of-00001.parquet",),
        "license": "see dataset card",
    },
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def http_get(url: str, accept: str | None = None, attempts: int = 4) -> bytes:
    headers = {"User-Agent": "gamma-algorithm-solver-fetch"}
    if accept:
        headers["Accept"] = accept
    last: Exception | None = None
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=120) as r:
                return r.read()
        except Exception as exc:  # retried, then re-raised
            last = exc
            time.sleep(2 ** attempt)
    raise RuntimeError(f"fetch failed after {attempts} attempts: {url}: {last}")


def fetch_hf_datasets(records: list[dict]) -> None:
    from huggingface_hub import HfApi, hf_hub_download

    api = HfApi()
    for spec in HF_DATASET_FILES:
        info = api.dataset_info(spec["repo"])
        revision = info.sha
        for name in spec["files"]:
            target_dir = RAW_DIR / spec["repo"].replace("/", "__")
            local = Path(
                hf_hub_download(
                    repo_id=spec["repo"],
                    filename=name,
                    repo_type="dataset",
                    revision=revision,
                    local_dir=target_dir,
                )
            )
            records.append(
                {
                    "source": f"hf-dataset:{spec['repo']}",
                    "revision": revision,
                    "file": name,
                    "path": str(local.relative_to(LANE_ROOT)),
                    "bytes": local.stat().st_size,
                    "sha256": sha256_file(local),
                    "license": spec["license"],
                }
            )
            print(f"[fetch] {spec['repo']}/{name} {local.stat().st_size:,} B", flush=True)


def fetch_doocs(records: list[dict]) -> None:
    api = f"https://api.github.com/repos/{DOOCS_REPO}"
    gh = "application/vnd.github+json"
    root = json.loads(http_get(f"{api}/git/trees/{DOOCS_COMMIT}", gh))
    solution = next(entry for entry in root["tree"] if entry["path"] == "solution")
    tree = json.loads(http_get(f"{api}/git/trees/{solution['sha']}?recursive=1", gh))
    if tree.get("truncated"):
        raise RuntimeError("doocs solution tree listing truncated; refusing a partial import")
    wanted = [
        entry
        for entry in tree["tree"]
        if entry["type"] == "blob"
        and (entry["path"] == "result.json" or entry["path"].endswith("/Solution.py"))
    ]
    target = RAW_DIR / "doocs__leetcode" / "solution"

    def one(entry: dict) -> dict:
        path = target / entry["path"]
        if path.exists() and git_blob_sha(path.read_bytes()) == entry["sha"]:
            data = path.read_bytes()
        else:
            raw = f"https://raw.githubusercontent.com/{DOOCS_REPO}/{DOOCS_COMMIT}/solution/{urllib.parse.quote(entry['path'])}"
            data = http_get(raw)
            if git_blob_sha(data) != entry["sha"]:
                raise RuntimeError(f"doocs blob hash mismatch: {entry['path']}")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        return {"path": entry["path"], "bytes": len(data), "git_blob_sha": entry["sha"]}

    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as pool:
        files = list(pool.map(one, wanted))
    total = sum(item["bytes"] for item in files)
    records.append(
        {
            "source": f"github:{DOOCS_REPO}",
            "revision": DOOCS_COMMIT,
            "file": "solution/result.json + solution/**/Solution.py",
            "path": str(target.relative_to(LANE_ROOT)),
            "bytes": total,
            "file_count": len(files),
            "verification": "every file matched its git blob sha at the pinned commit",
            "license": "CC-BY-SA-4.0; commercial reprints require author authorization; research use only",
        }
    )
    print(f"[fetch] doocs {len(files)} files {total:,} B", flush=True)


def fetch_model(records: list[dict]) -> None:
    from huggingface_hub import HfApi, snapshot_download

    revision = HfApi().model_info(MODEL_REPO).sha
    local = Path(snapshot_download(repo_id=MODEL_REPO, revision=revision))
    files = sorted(p for p in local.rglob("*") if p.is_file())
    records.append(
        {
            "source": f"hf-model:{MODEL_REPO}",
            "revision": revision,
            "path": str(local),
            "bytes": sum(p.stat().st_size for p in files),
            "files": {
                str(p.relative_to(local)): sha256_file(p) for p in files if p.suffix in {".safetensors", ".json"}
            },
            "license": "apache-2.0",
        }
    )
    print(f"[fetch] model {MODEL_REPO}@{revision} -> {local}", flush=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", choices=("datasets", "doocs", "model"), action="append")
    args = parser.parse_args(argv)
    parts = args.only or ["datasets", "doocs", "model"]
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    existing = json.loads(MANIFEST_PATH.read_text()) if MANIFEST_PATH.exists() else {"records": []}
    keep = [r for r in existing["records"] if not any(r["source"].startswith(p) for p in _prefixes(parts))]
    records: list[dict] = []
    if "datasets" in parts:
        fetch_hf_datasets(records)
    if "doocs" in parts:
        fetch_doocs(records)
    if "model" in parts:
        fetch_model(records)
    MANIFEST_PATH.write_text(json.dumps({"records": keep + records}, indent=2) + "\n")
    print(f"[fetch] manifest -> {MANIFEST_PATH}", flush=True)
    return 0


def _prefixes(parts: list[str]) -> list[str]:
    mapping = {"datasets": "hf-dataset:", "doocs": "github:", "model": "hf-model:"}
    return [mapping[p] for p in parts]


if __name__ == "__main__":
    sys.exit(main())
