#!/usr/bin/env bash
set -euo pipefail

PY=".venv/bin/python"
if [[ ! -x "$PY" ]]; then
  PY="python3"
fi

MODEL_A="${1:-gemma-1b}"
MODEL_B="${2:-gemma-2b}"
PROMPT="${3:-Write two sentences about reproducible model evaluation.}"
STEPS="${STEPS:-32}"

CMD=(
  "$PY" tools/run_mind_meld_cli.py "$MODEL_A" "$MODEL_B"
  --blend dynamic
  --strategy pattern
  --prompt "$PROMPT"
  --steps "$STEPS"
  --summary-only
  --headless
  --no-step-delay
  --shared-chat-template
  --meld-diagnostics
)

if [[ "${DRY_RUN:-0}" == "1" ]]; then
  printf '%q ' "${CMD[@]}"
  echo
  exit 0
fi

exec "${CMD[@]}"
