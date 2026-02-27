#!/usr/bin/env bash
set -euo pipefail

# Wrapper for TranslateGemma distillation end-to-end.
# By default it:
# 1) builds triplets from projects/distillation/translation/bitext,
# 2) splits triplets into train/eval,
# 3) trains with train_translate_distill.py,
# 4) evaluates on held-out eval pairs (optional, optional teacher baseline).
#
# Usage:
#   bash projects/distillation/translation/training/run_translation_distill.sh A_then_B
#   bash projects/distillation/translation/training/run_translation_distill.sh mixed_from_start
#
# Override any default via environment variables, e.g.:
#   TOTAL_STEPS=20000 SFT_STEPS=10000 DEVICE=cuda RUN_NAME=exp02 \
#   bash .../run_translation_distill.sh A_then_B

SCHEDULE="${1:-A_then_B}"
if [[ "$SCHEDULE" != "A_then_B" && "$SCHEDULE" != "mixed_from_start" ]]; then
  echo "Invalid schedule: $SCHEDULE"
  echo "Expected: A_then_B | mixed_from_start"
  exit 1
fi

PYTHON_BIN="${PYTHON_BIN:-}"
if [[ -z "$PYTHON_BIN" ]]; then
  if [[ -x ".venv/bin/python" ]]; then
    PYTHON_BIN=".venv/bin/python"
  elif [[ -x "gamma/.venv/bin/python" ]]; then
    PYTHON_BIN="gamma/.venv/bin/python"
  else
    PYTHON_BIN="python3"
  fi
fi
TRAINER="${TRAINER:-projects/distillation/translation/training/train_translate_distill.py}"
PAIRS="${PAIRS:-projects/distillation/translation/training_data/translate_distill_pairs.jsonl}"
MAKE_PAIRS="${MAKE_PAIRS:-1}"
PAIR_BUILDER="${PAIR_BUILDER:-projects/distillation/translation/training/make_translate_distill_pairs.py}"
SEED_DIR="${SEED_DIR:-projects/distillation/translation/bitext}"
PAIRS_SUMMARY_OUT="${PAIRS_SUMMARY_OUT:-${PAIRS%.jsonl}.summary.json}"
PAIRS_PER_PAIR="${PAIRS_PER_PAIR:-1250}"
PAIRS_MIN_CHARS="${PAIRS_MIN_CHARS:-8}"
PAIRS_NEG_STRATEGY="${PAIRS_NEG_STRATEGY:-lexical_hard}"
SPLIT_PAIRS="${SPLIT_PAIRS:-1}"
PAIR_SPLITTER="${PAIR_SPLITTER:-projects/distillation/translation/training/split_translate_distill_pairs.py}"
TRAIN_PAIRS="${TRAIN_PAIRS:-${PAIRS%.jsonl}.train.jsonl}"
EVAL_PAIRS="${EVAL_PAIRS:-${PAIRS%.jsonl}.eval.jsonl}"
EVAL_FRACTION="${EVAL_FRACTION:-0.10}"
EVAL_MAX_ROWS="${EVAL_MAX_ROWS:-0}"
EVAL_MIN_EVAL_PER_PAIR="${EVAL_MIN_EVAL_PER_PAIR:-1}"
TEACHER_MODEL="${TEACHER_MODEL:-google/translategemma-4b-it}"
STUDENT_MODEL="${STUDENT_MODEL:-google/translategemma-4b-it}"
SOURCE_LANGS="${SOURCE_LANGS:-fr,de,it,pt,ar,hi,ja,zh}"
TARGET_LANGS="${TARGET_LANGS:-en,es}"
OUT_ROOT="${OUT_ROOT:-projects/distillation/translation/runs/exp01}"
RUN_NAME="${RUN_NAME:-exp01}"
SUMMARY_OUT="${SUMMARY_OUT:-$OUT_ROOT/$RUN_NAME/train_summary.json}"
EVAL_ENABLED="${EVAL_ENABLED:-1}"
EVAL_SCRIPT="${EVAL_SCRIPT:-projects/distillation/translation/eval/run_translate_distill_eval.py}"
EVAL_OUT_DIR="${EVAL_OUT_DIR:-$OUT_ROOT/$RUN_NAME/eval}"
EVAL_MODEL="${EVAL_MODEL:-$OUT_ROOT/$RUN_NAME/final}"
EVAL_TEACHER_MODEL="${EVAL_TEACHER_MODEL:-$TEACHER_MODEL}"
EVAL_SAMPLES="${EVAL_SAMPLES:-0}"
EVAL_BATCH_SIZE="${EVAL_BATCH_SIZE:-2}"
EVAL_MAX_PROMPT_LENGTH="${EVAL_MAX_PROMPT_LENGTH:-256}"
EVAL_MAX_NEW_TOKENS="${EVAL_MAX_NEW_TOKENS:-192}"
EVAL_DO_SAMPLE="${EVAL_DO_SAMPLE:-0}"
EVAL_TEMPERATURE="${EVAL_TEMPERATURE:-0.0}"
EVAL_TOP_P="${EVAL_TOP_P:-1.0}"
EVAL_TOP_K="${EVAL_TOP_K:-50}"
EVAL_BLEU="${EVAL_BLEU:-1}"
EVAL_CHRF="${EVAL_CHRF:-1}"
EVAL_COMET="${EVAL_COMET:-0}"
EVAL_COMET_MODEL="${EVAL_COMET_MODEL:-Unbabel/wmt22-comet-da}"
EVAL_COMET_BATCH_SIZE="${EVAL_COMET_BATCH_SIZE:-8}"
EVAL_ALLOW_DOWNLOAD="${EVAL_ALLOW_DOWNLOAD:-${ALLOW_DOWNLOAD:-1}}"
TOTAL_STEPS="${TOTAL_STEPS:-100000}"
SFT_STEPS="${SFT_STEPS:-50000}"
BATCH_SIZE="${BATCH_SIZE:-1}"
LR="${LR:-2e-5}"
LOG_EVERY="${LOG_EVERY:-20}"
SAVE_EVERY="${SAVE_EVERY:-200}"
LAMBDA_KD="${LAMBDA_KD:-0.5}"
MU_TRIPLET="${MU_TRIPLET:-0.1}"
MARGIN="${MARGIN:-0.2}"
ENABLE_LORA="${ENABLE_LORA:-1}"
LORA_RANK="${LORA_RANK:-16}"
LORA_ALPHA="${LORA_ALPHA:-32}"
LORA_DROPOUT="${LORA_DROPOUT:-0.05}"
DRY_RUN="${DRY_RUN:-0}"
DEVICE="${DEVICE:-cuda}"
ALLOW_DOWNLOAD="${ALLOW_DOWNLOAD:-1}"
SKIP_TRAIN="${SKIP_TRAIN:-0}"
RESUME="${RESUME:-0}"
RESUME_FROM="${RESUME_FROM:-}"

if [[ "$MAKE_PAIRS" == "1" ]]; then
  src_csv="$SOURCE_LANGS"
  tgt_csv="$TARGET_LANGS"
  IFS=',' read -r -a src_langs <<< "$src_csv"
  IFS=',' read -r -a tgt_langs <<< "$tgt_csv"

  pair_args=()
  for src in "${src_langs[@]}"; do
    src="$(echo "$src" | xargs)"
    [[ -z "$src" ]] && continue
    src_file="$SEED_DIR/${src}.txt"
    for tgt in "${tgt_langs[@]}"; do
      tgt="$(echo "$tgt" | xargs)"
      [[ -z "$tgt" ]] && continue
      tgt_file="$SEED_DIR/${src}_to_${tgt}.txt"
      if [[ ! -f "$src_file" ]]; then
        echo "Missing source seed file: $src_file"
        exit 1
      fi
      if [[ ! -f "$tgt_file" ]]; then
        echo "Missing target seed file: $tgt_file"
        exit 1
      fi
      pair_args+=(--pair-file "$src" "$tgt" "$src_file" "$tgt_file")
    done
  done

  if [[ "${#pair_args[@]}" -eq 0 ]]; then
    echo "No pair-file arguments built from SOURCE_LANGS=$SOURCE_LANGS TARGET_LANGS=$TARGET_LANGS"
    exit 1
  fi

  mkdir -p "$(dirname "$PAIRS")"
  mkdir -p "$(dirname "$PAIRS_SUMMARY_OUT")"
  pair_cmd=(
    "$PYTHON_BIN" "$PAIR_BUILDER"
    "${pair_args[@]}"
    --target-langs "$TARGET_LANGS"
    --pairs-per-pair "$PAIRS_PER_PAIR"
    --min-chars "$PAIRS_MIN_CHARS"
    --neg-strategy "$PAIRS_NEG_STRATEGY"
    --out "$PAIRS"
    --summary-out "$PAIRS_SUMMARY_OUT"
  )
  echo "+ ${pair_cmd[*]}"
  if [[ "$DRY_RUN" == "1" ]]; then
    :
  else
    "${pair_cmd[@]}"
  fi
fi

TRAIN_PAIRS_PATH="$TRAIN_PAIRS"
EVAL_PAIRS_PATH="$EVAL_PAIRS"
if [[ "$SPLIT_PAIRS" == "1" ]]; then
  mkdir -p "$(dirname "$TRAIN_PAIRS_PATH")" "$(dirname "$EVAL_PAIRS_PATH")"
  pair_split_cmd=(
    "$PYTHON_BIN" "$PAIR_SPLITTER"
    --pairs "$PAIRS"
    --train-out "$TRAIN_PAIRS_PATH"
    --eval-out "$EVAL_PAIRS_PATH"
    --eval-fraction "$EVAL_FRACTION"
    --eval-max-rows "$EVAL_MAX_ROWS"
    --min-eval-per-pair "$EVAL_MIN_EVAL_PER_PAIR"
  )
  echo "+ ${pair_split_cmd[*]}"
  if [[ "$DRY_RUN" == "1" ]]; then
    :
  else
    "${pair_split_cmd[@]}"
  fi
else
  TRAIN_PAIRS_PATH="$PAIRS"
  if [[ ! -f "$EVAL_PAIRS_PATH" ]]; then
    EVAL_PAIRS_PATH="$PAIRS"
  fi
fi

if [[ "$SKIP_TRAIN" == "0" ]]; then
  cmd=(
    "$PYTHON_BIN" "$TRAINER"
    --pairs "$TRAIN_PAIRS_PATH"
    --teacher-model "$TEACHER_MODEL"
    --student-model "$STUDENT_MODEL"
    --source-langs "$SOURCE_LANGS"
    --target-langs "$TARGET_LANGS"
    --out-root "$OUT_ROOT"
    --run-name "$RUN_NAME"
    --schedule "$SCHEDULE"
    --total-steps "$TOTAL_STEPS"
    --batch-size "$BATCH_SIZE"
    --lr "$LR"
    --log-every "$LOG_EVERY"
    --save-every "$SAVE_EVERY"
    --lambda-kd "$LAMBDA_KD"
    --mu-triplet "$MU_TRIPLET"
    --margin "$MARGIN"
    --device "$DEVICE"
    --summary-out "$SUMMARY_OUT"
  )
  if [[ "$RESUME" == "1" ]]; then
    cmd+=(--resume)
    if [[ -n "${RESUME_FROM}" ]]; then
      cmd+=(--resume-from "$RESUME_FROM")
    fi
  fi

  if [[ "$SCHEDULE" == "A_then_B" ]]; then
    cmd+=(--sft-steps "$SFT_STEPS")
  fi

  if [[ "$ENABLE_LORA" == "1" ]]; then
    cmd+=(--enable-lora --lora-rank "$LORA_RANK" --lora-alpha "$LORA_ALPHA" --lora-dropout "$LORA_DROPOUT")
  fi

  if [[ "$ALLOW_DOWNLOAD" == "1" ]]; then
    cmd+=(--allow-download)
  fi

  echo "+ ${cmd[*]}"
  if [[ "$DRY_RUN" == "1" ]]; then
    :
  else
    "${cmd[@]}"
  fi
else
  echo "SKIP_TRAIN=1: skipping trainer."
fi

if [[ "$EVAL_ENABLED" == "1" ]]; then
  if [[ ! -f "$EVAL_PAIRS_PATH" ]]; then
    echo "No eval data at $EVAL_PAIRS_PATH, skipping eval."
    exit 0
  fi
  eval_cmd=(
    "$PYTHON_BIN" "$EVAL_SCRIPT"
    --pairs "$EVAL_PAIRS_PATH"
    --model "$EVAL_MODEL"
    --source-langs "$SOURCE_LANGS"
    --target-langs "$TARGET_LANGS"
    --out-dir "$EVAL_OUT_DIR"
    --eval-samples "$EVAL_SAMPLES"
    --batch-size "$EVAL_BATCH_SIZE"
    --max-prompt-length "$EVAL_MAX_PROMPT_LENGTH"
    --max-new-tokens "$EVAL_MAX_NEW_TOKENS"
    --device "$DEVICE"
    --top-k "$EVAL_TOP_K"
    --top-p "$EVAL_TOP_P"
    --temperature "$EVAL_TEMPERATURE"
    --student-summary "$EVAL_OUT_DIR/student_eval_summary.json"
    --teacher-summary "$EVAL_OUT_DIR/teacher_eval_summary.json"
    --compare-summary "$EVAL_OUT_DIR/compare_eval_summary.json"
    --student-predictions "$EVAL_OUT_DIR/student_predictions.jsonl"
    --teacher-predictions "$EVAL_OUT_DIR/teacher_predictions.jsonl"
  )
  if [[ "$EVAL_DO_SAMPLE" == "1" ]]; then
    eval_cmd+=(--do-sample)
  fi
  if [[ "$EVAL_BLEU" == "1" ]]; then
    eval_cmd+=(--eval-bleu)
  fi
  if [[ "$EVAL_CHRF" == "1" ]]; then
    eval_cmd+=(--eval-chrf)
  fi
  if [[ "$EVAL_COMET" == "1" ]]; then
    eval_cmd+=(--eval-comet --comet-model "$EVAL_COMET_MODEL" --comet-batch-size "$EVAL_COMET_BATCH_SIZE")
  fi
  if [[ -n "$EVAL_TEACHER_MODEL" ]]; then
    eval_cmd+=(--teacher-model "$EVAL_TEACHER_MODEL")
  fi
  if [[ "$EVAL_ALLOW_DOWNLOAD" == "1" ]]; then
    eval_cmd+=(--allow-download)
  fi

  echo "+ ${eval_cmd[*]}"
  if [[ "$DRY_RUN" == "1" ]]; then
    :
  else
    "${eval_cmd[@]}"
  fi
fi
