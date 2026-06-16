#!/usr/bin/env bash
set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_ROOT="$(cd "$ROOT/../.." && pwd)"
OUT_DIR="$ROOT/run_logs"
mkdir -p "$OUT_DIR"

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
  pgrep -af 'projects/enwiki9/lib/driver.py|cmix21-mmap|enwiki9-heavy.lock|bench.py' || true
  echo
  echo "[candidate_audit_summary]"
  python3 "$ROOT/tools/candidate_audit.py" --json 2>/dev/null \
    | python3 -c 'import json,sys; d=json.load(sys.stdin); print(json.dumps(d.get("summary",{}), sort_keys=True))' \
    || true
  echo
  echo "[upper_bound_certificate_excerpt]"
  sed -n '1,120p' "$ROOT/UPPER_BOUND_CERTIFICATE.md" 2>/dev/null || true
  echo
  echo "[recent_cmix21_results]"
  find "$ROOT/results" -maxdepth 2 -type f -name '*.json' \
    -path '*cmix21_text_mmap_paq5_ppmd50m_fxcmidx13div2_rcm32_bufthirtysecond_minmaps_v1*' \
    -printf '%TY-%Tm-%Td %TH:%TM:%TS %s %p\n' 2>/dev/null \
    | sort | tail -20 || true
  echo
  echo "[lock_safe_reports]"
  ls -l "$ROOT/I_SSA_LOCK_SAFE_REPORT.md" "$ROOT/CMIX21_LOCK_SAFE_QUEUE.md" 2>/dev/null || true
} > "$OUT" 2>&1

echo "$OUT"
