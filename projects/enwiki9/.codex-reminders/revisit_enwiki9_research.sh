#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
LOG="$HERE/revisit_enwiki9_research.log"
UNIT="codex-enwiki9-research-revisit"
PROTOCOL="$HERE/wakeup_protocol.md"
MESSAGE="Revisit enwiki9 graph-token diffusion compression research; apply wakeup_protocol.md; schedule the next 60m reminder."

{
  printf '[%s] %s\n' "$(date -Iseconds)" "$MESSAGE"
  printf 'protocol=%s\n' "$PROTOCOL"
} >> "$LOG"

if command -v notify-send >/dev/null 2>&1; then
  notify-send "Codex reminder" "$MESSAGE" || true
fi

systemd-run --user \
  --unit="$UNIT" \
  --on-active=60m \
  --description="Codex enwiki9 research revisit reminder" \
  "$HERE/revisit_enwiki9_research.sh" >/dev/null
