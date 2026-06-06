#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROMPT_FILE="$HERE/enwiki9_persona_prompt.md"
LOG="$HERE/enwiki9_persona_reminder.log"

schedule_next() {
  local delay_min="$1"
  local unit="codex-enwiki9-persona-reminder-$(date +%s)-$RANDOM"

  systemd-run --user \
    --unit="$unit" \
    --on-active="${delay_min}m" \
    --description="Codex enwiki9 persona reminder" \
    "$HERE/enwiki9_persona_reminder.sh" >/dev/null

  printf '%s\n' "$unit"
}

main() {
  local prompt
  prompt="$(cat "$PROMPT_FILE")"

  local next_delay_min=$((30 + RANDOM % 11))
  local next_unit
  next_unit="$(schedule_next "$next_delay_min")"

  {
    printf '[%s] enwiki9 persona reminder\n' "$(date -Iseconds)"
    printf '%s\n' "$prompt"
    printf 'Next reminder scheduled by %s with randomized delay in the 30-40 minute window.\n' "$next_unit"
  } >> "$LOG"

  if command -v notify-send >/dev/null 2>&1; then
    notify-send \
      "enwiki9 persona reminder" \
      "$prompt

Next: set another reminder in the 30-40 minute window; already scheduled by $next_unit." || true
  fi
}

main "$@"
