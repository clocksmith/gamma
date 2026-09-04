#!/usr/bin/env bash
set -euo pipefail

INPUT_PATH="${1:-projects/distillation/translation/runs}"

if [[ ! -d "$INPUT_PATH" ]]; then
  echo "Path not found: $INPUT_PATH"
  exit 1
fi

collect_stage_dirs() {
  local path="$1"
  if [[ "$(basename "$path")" =~ ^stage_[ab]$ ]]; then
    printf "%s\n" "$path"
    return 0
  fi

  find "$path" -type d \( -name stage_a -o -name stage_b \) | sort -V
}

analyze_stage() {
  local stage_dir="$1"
  local checkpoints=()
  local latest_valid=""

  mapfile -t checkpoints < <(find "$stage_dir" -maxdepth 1 -type d -name "checkpoint-*" | sort -V)

  echo
  echo "Stage: $stage_dir"
  if [[ "${#checkpoints[@]}" -eq 0 ]]; then
    echo "  no checkpoints found"
    return 0
  fi

  for ckpt in "${checkpoints[@]}"; do
    local training_state="$ckpt/training_state.pt"
    local zero_files
    local status="INVALID"
    local reason=()

    zero_files=$(find "$ckpt" -type f -size 0 | wc -l | tr -d ' ')

    if [[ ! -s "$training_state" ]]; then
      reason+=("missing_or_empty_training_state")
    fi
    if [[ "$zero_files" != "0" ]]; then
      reason+=("zero_byte_files=$zero_files")
    fi

    if [[ "${#reason[@]}" -eq 0 ]]; then
      status="VALID"
      latest_valid="$ckpt"
    fi

    echo "  $status $(basename "$ckpt")"
    if [[ "${#reason[@]}" -gt 0 ]]; then
      echo "    reason: ${reason[*]}"
    fi
  done

  if [[ -n "$latest_valid" ]]; then
    echo "  latest_valid: $latest_valid"
    echo "  resume_example: RESUME=1 RESUME_FROM=$latest_valid bash projects/distillation/translation/training/run_translation_distill.sh A_then_B"
  else
    echo "  latest_valid: none"
  fi
}

mapfile -t STAGE_DIRS < <(collect_stage_dirs "$INPUT_PATH")

if [[ "${#STAGE_DIRS[@]}" -eq 0 ]]; then
  echo "No stage_a/stage_b directories found under: $INPUT_PATH"
  exit 1
fi

for stage in "${STAGE_DIRS[@]}"; do
  analyze_stage "$stage"
done
