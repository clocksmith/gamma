#!/usr/bin/env bash
set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_ROOT="$(cd "$ROOT/../.." && pwd)"
OUT_DIR="$ROOT/run_logs"
mkdir -p "$OUT_DIR"

DEFAULT_ACTIVE_CANDIDATE="cmix21_text_mmap_paq5_ppmd20352k_fxcm2_fxcmrcm20_ppmdguard2_rcm32_buffull_minmaps_v1"
DEFAULT_ACTIVE_SCOPE="10000000"
read -r ACTIVE_CANDIDATE ACTIVE_SCOPE < <(
  python3 - "$ROOT/upper_bound_certificate.json" "$DEFAULT_ACTIVE_CANDIDATE" "$DEFAULT_ACTIVE_SCOPE" <<'PY'
import json
import pathlib
import sys


cert_path = pathlib.Path(sys.argv[1])
default_candidate = sys.argv[2]
default_scope = sys.argv[3]

try:
    cert = json.loads(cert_path.read_text())
except (OSError, json.JSONDecodeError):
    print(default_candidate, default_scope)
    raise SystemExit

for row in cert.get("top_status", []):
    if not isinstance(row, dict):
        continue
    if row.get("label") != "active gate":
        continue
    candidate = row.get("program_id")
    scope = row.get("scope_bytes")
    if isinstance(candidate, str) and isinstance(scope, int):
        print(candidate, scope)
        raise SystemExit

print(default_candidate, default_scope)
PY
)
RSS_GUARD_KIB="10485760"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="$OUT_DIR/enwiki9_delayed_status_${STAMP}.log"

{
  echo "[timestamp_utc] $(date -u --iso-8601=seconds)"
  echo "[repo] $REPO_ROOT"
  echo
  echo "[git_status]"
  git -C "$REPO_ROOT" status --short --branch || true
  echo
  echo "[heavy_lock]"
  flock -n -E 75 /tmp/enwiki9-heavy.lock true
  echo "lock_rc=$?"
  echo
  echo "[runner_processes]"
  pgrep -af 'projects/enwiki9/lib/driver.py|cmix21-mmap|enwiki9-heavy.lock|run_with_rss_guard' || true
  echo
  echo "[runner_process_table]"
  ps -eo pid,ppid,pgid,sid,stat,rss,args \
    | grep -E 'projects/enwiki9/lib/driver.py|cmix21-mmap|enwiki9-heavy.lock|run_with_rss_guard' \
    | grep -v grep || true
  echo
  echo "[active_rss_margin]"
  RSS_GUARD_KIB="$RSS_GUARD_KIB" python3 - <<'PY' || true
import os
import subprocess


guard = int(os.environ["RSS_GUARD_KIB"])
rows = subprocess.run(["ps", "-eo", "pid,rss,args"], check=True, text=True, capture_output=True).stdout.splitlines()[1:]
cmix_rows = []
tree_rows = []
for row in rows:
    parts = row.strip().split(None, 2)
    if len(parts) < 3:
        continue
    pid = int(parts[0])
    rss = int(parts[1])
    args = parts[2]
    if "projects/enwiki9/lib/driver.py" in args or "cmix21-mmap-bin" in args:
        tree_rows.append((pid, rss, args))
    if "cmix21-mmap-bin" in args:
        cmix_rows.append((pid, rss, args))

if not cmix_rows:
    print("none")
else:
    pid, rss, _ = max(cmix_rows, key=lambda item: item[1])
    margin = guard - rss
    print(f"guard_kib={guard}")
    print(f"max_cmix_pid={pid}")
    print(f"max_cmix_rss_kib={rss}")
    print(f"single_process_margin_kib={margin}")
    if tree_rows:
        tree_total = sum(row[1] for row in tree_rows)
        print(f"driver_plus_cmix_rss_kib={tree_total}")
PY
  echo
  echo "[unguarded_cmix_processes]"
  python3 - <<'PY' || true
import pathlib
import subprocess


def children_of(pid: int) -> list[int]:
    path = pathlib.Path("/proc") / str(pid) / "task" / str(pid) / "children"
    try:
        text = path.read_text().strip()
    except OSError:
        return []
    return [int(part) for part in text.split()] if text else []


def descendants(pid: int) -> set[int]:
    out = set()
    stack = [pid]
    while stack:
        current = stack.pop()
        if current in out:
            continue
        out.add(current)
        stack.extend(children_of(current))
    return out


rows = subprocess.run(["ps", "-eo", "pid,args"], check=True, text=True, capture_output=True).stdout.splitlines()[1:]
guarded: set[int] = set()
cmix: list[tuple[int, str]] = []
for row in rows:
    raw_pid, _, args = row.strip().partition(" ")
    if not raw_pid:
        continue
    pid = int(raw_pid)
    if "run_with_rss_guard.py" in args:
        guarded |= descendants(pid)
    if "cmix21-mmap-bin" in args:
        cmix.append((pid, args))

orphans = [(pid, args) for pid, args in cmix if pid not in guarded]
if not orphans:
    print("none")
else:
    for pid, args in orphans:
        print(f"{pid} {args}")
PY
  echo
  echo "[active_temp_usage]"
  ACTIVE_SCOPE="$ACTIVE_SCOPE" python3 - <<'PY' || true
import os
import pathlib
import shlex
import subprocess


def path_size(path: pathlib.Path) -> int | None:
    try:
        if path.is_file():
            return path.stat().st_size
        total = 0
        for root, _, files in os.walk(path):
            for name in files:
                fp = pathlib.Path(root) / name
                try:
                    total += fp.stat().st_size
                except OSError:
                    pass
        return total
    except OSError:
        return None


rows = subprocess.run(["ps", "-eo", "pid,args"], check=True, text=True, capture_output=True).stdout.splitlines()[1:]
try:
    active_scope = int(os.environ.get("ACTIVE_SCOPE", "0"))
except ValueError:
    active_scope = 0
printed = False
for row in rows:
    raw_pid, _, args = row.strip().partition(" ")
    if "cmix21-mmap-bin" not in args:
        continue
    pid = int(raw_pid)
    try:
        parts = shlex.split(args)
    except ValueError:
        parts = args.split()
    if "-d" in parts:
        mode = "decode"
    elif "-t" in parts:
        mode = "text_compress"
    elif "-c" in parts:
        mode = "compress"
    elif "-n" in parts:
        mode = "no_preprocess_compress"
    elif "-s" in parts:
        mode = "preprocess_only"
    else:
        mode = "unknown"
    paths = []
    for part in parts:
        if not part.startswith("/tmp/"):
            continue
        path = pathlib.Path(part)
        if path.exists():
            paths.append(path)
        temp_path = pathlib.Path(str(path) + ".cmix.temp")
        if temp_path.exists():
            paths.append(temp_path)
    if not paths:
        continue
    printed = True
    print(f"pid={pid}")
    print(f"  mode={mode}")
    for path in paths:
        size = path_size(path)
        if size is not None:
            print(f"  {size} {path}")
            if mode == "decode" and active_scope > 0 and str(path).endswith(".cmix.temp"):
                capped = min(size, active_scope)
                percent = (100.0 * capped) / active_scope
                remaining = max(active_scope - capped, 0)
                print(f"  decode_scope_progress={capped}/{active_scope} ({percent:.3f}%)")
                print(f"  decode_remaining_scope_bytes={remaining}")
if not printed:
    print("none")
PY
  echo
  echo "[active_gate_decider]"
  python3 "$ROOT/tools/cmix21_gate_decider.py" "$ACTIVE_CANDIDATE" --scope "$ACTIVE_SCOPE" || true
  echo
  echo "[active_candidate_recent_results]"
  find "$ROOT/results/$ACTIVE_CANDIDATE" -maxdepth 1 -type f \
    -printf '%TY-%Tm-%Td %TH:%TM:%TS %s %p\n' 2>/dev/null \
    | sort | tail -20 || true
  echo
  echo "[candidate_audit_summary]"
  python3 "$ROOT/tools/candidate_audit.py" --json 2>/dev/null \
    | python3 -c 'import json,sys; d=json.load(sys.stdin); print(json.dumps(d.get("summary",{}), sort_keys=True))' \
    || true
  echo
  echo "[upper_bound_certificate_excerpt]"
  sed -n '1,120p' "$ROOT/UPPER_BOUND_CERTIFICATE.md" 2>/dev/null || true
  echo
  echo "[lock_safe_reports]"
  ls -l "$ROOT/I_SSA_LOCK_SAFE_REPORT.md" "$ROOT/CMIX21_LOCK_SAFE_QUEUE.md" 2>/dev/null || true
} > "$OUT" 2>&1

ln -sfn "$(basename "$OUT")" "$OUT_DIR/enwiki9_delayed_status_latest.log"
echo "$OUT"
