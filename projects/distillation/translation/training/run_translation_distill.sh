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
#
# Troubleshooting (ROCm vs CPU fallback):
#   projects/distillation/translation/training/TROUBLESHOOTING.md

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
PAIRS_HARD_NEG_POOL="${PAIRS_HARD_NEG_POOL:-128}"
PAIRS_MAX_ROWS_PER_INPUT="${PAIRS_MAX_ROWS_PER_INPUT:-0}"
PAIR_ALLOW_LINE_MISMATCH="${PAIR_ALLOW_LINE_MISMATCH:-0}"
SPLIT_PAIRS="${SPLIT_PAIRS:-1}"
PAIR_SPLITTER="${PAIR_SPLITTER:-projects/distillation/translation/training/split_translate_distill_pairs.py}"
TRAIN_PAIRS="${TRAIN_PAIRS:-${PAIRS%.jsonl}.train.jsonl}"
EVAL_PAIRS="${EVAL_PAIRS:-${PAIRS%.jsonl}.eval.jsonl}"
EVAL_FRACTION="${EVAL_FRACTION:-0.10}"
EVAL_MAX_ROWS="${EVAL_MAX_ROWS:-0}"
EVAL_MIN_EVAL_PER_PAIR="${EVAL_MIN_EVAL_PER_PAIR:-1}"
TEACHER_MODEL="${TEACHER_MODEL:-google/translategemma-4b-it}"
STUDENT_MODEL="${STUDENT_MODEL:-google/translategemma-4b-it}"
SOURCE_LANGS="${SOURCE_LANGS:-en,es}"
TARGET_LANGS="${TARGET_LANGS:-en,es}"
VOCAB_SUBSET_DIR="${VOCAB_SUBSET_DIR:-}"
TOKENIZER_MODEL="${TOKENIZER_MODEL:-}"
SUBSET_ENABLED="${SUBSET_ENABLED:-1}"
SUBSET_TOP_K="${SUBSET_TOP_K:-50000}"
SUBSET_MIN_COUNT="${SUBSET_MIN_COUNT:-2}"
SUBSET_MODEL="${SUBSET_MODEL:-$STUDENT_MODEL}"
SUBSET_MIN_TEXT_CHARS="${SUBSET_MIN_TEXT_CHARS:-4}"
SUBSET_TEXT="${SUBSET_TEXT:-}"
SUBSET_TEXT_BUILDER="${SUBSET_TEXT_BUILDER:-projects/distillation/translation/pipeline/build_vocab_subset_text.py}"
SUBSET_FILL_TO_TOP_K="${SUBSET_FILL_TO_TOP_K:-1}"
SUBSET_FILL_STRATEGY="${SUBSET_FILL_STRATEGY:-spm_score}"
SUBSET_DTYPE="${SUBSET_DTYPE:-auto}"
SUBSET_WRITE_CHECKPOINT="${SUBSET_WRITE_CHECKPOINT:-1}"
SUBSET_ALSO_PRUNE_OUTPUT="${SUBSET_ALSO_PRUNE_OUTPUT:-0}"
SUBSET_ALLOW_DOWNLOAD="${SUBSET_ALLOW_DOWNLOAD:-0}"
SUBSET_MAX_LINES="${SUBSET_MAX_LINES:-0}"
SUBSET_FOR_CAUSAL_LM="${SUBSET_FOR_CAUSAL_LM:-1}"
OUT_ROOT="${OUT_ROOT:-projects/distillation/translation/runs/exp01}"
RUN_NAME="${RUN_NAME:-exp01}"
SUBSET_DIR="${SUBSET_DIR:-$OUT_ROOT/$RUN_NAME/vocab_subset}"
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
ENABLE_LORA="${ENABLE_LORA:-0}"
LORA_RANK="${LORA_RANK:-16}"
LORA_ALPHA="${LORA_ALPHA:-32}"
LORA_DROPOUT="${LORA_DROPOUT:-0.05}"
DRY_RUN="${DRY_RUN:-0}"
DEVICE="${DEVICE:-cuda}"
DTYPE="${DTYPE:-auto}"
ALLOW_DOWNLOAD="${ALLOW_DOWNLOAD:-1}"
SKIP_TRAIN="${SKIP_TRAIN:-0}"
AUTO_FALLBACK_TO_CPU="${AUTO_FALLBACK_TO_CPU:-0}"
RESUME="${RESUME:-0}"
RESUME_FROM="${RESUME_FROM:-}"
EFFECTIVE_STUDENT_MODEL="${STUDENT_MODEL}"

has_subset_artifacts() {
  local model_dir="$1"
  if [[ ! -d "$model_dir" ]]; then
    return 1
  fi
  if [[ ! -f "$model_dir/config.json" ]]; then
    return 1
  fi
  if [[ -f "$model_dir/model.safetensors" || -f "$model_dir/pytorch_model.bin" || -f "$model_dir/pytorch_model.bin.index.json" ]]; then
    return 0
  fi
  for _ckpt in "$model_dir"/*.safetensors "$model_dir"/*.bin; do
    if [[ -f "$_ckpt" ]]; then
      return 0
    fi
  done
  return 1
}

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
        if [[ "$src" == "$tgt" ]]; then
          continue
        fi
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
    --hard-neg-pool "$PAIRS_HARD_NEG_POOL"
    --out "$PAIRS"
    --summary-out "$PAIRS_SUMMARY_OUT"
    --max-rows-per-input "$PAIRS_MAX_ROWS_PER_INPUT"
  )
  if [[ "$PAIR_ALLOW_LINE_MISMATCH" == "1" ]]; then
    pair_cmd+=(--allow-mismatched-pair-lines)
  fi
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

if [[ "$SUBSET_ENABLED" == "1" ]]; then
  if [[ -z "$VOCAB_SUBSET_DIR" ]]; then
    VOCAB_SUBSET_DIR="$SUBSET_DIR"
  fi

  if [[ "$RESUME" == "1" ]] && [[ -f "$VOCAB_SUBSET_DIR/id_remap.json" ]]; then
    echo "[subset] skip: existing id_remap.json at $VOCAB_SUBSET_DIR"
  else
    subset_text_file="$OUT_ROOT/$RUN_NAME/subset_text_source.txt"
    mkdir -p "$(dirname "$subset_text_file")"
    pair_text_inputs=()
    pair_text_inputs+=("$TRAIN_PAIRS_PATH")
    if [[ "$TRAIN_PAIRS_PATH" != "$EVAL_PAIRS_PATH" ]]; then
      pair_text_inputs+=("$EVAL_PAIRS_PATH")
    fi

    IFS=',' read -r -a src_langs_csv <<< "$SOURCE_LANGS"
    IFS=',' read -r -a tgt_langs_csv <<< "$TARGET_LANGS"
    IFS=',' read -r -a subset_text_inputs <<< "$SUBSET_TEXT"

    raw_text_inputs=()
    for src in "${src_langs_csv[@]}"; do
      src="$(echo "$src" | xargs)"
      [[ -z "$src" ]] && continue
      src_file="$SEED_DIR/$src.txt"
      raw_text_inputs+=("$src_file")
      for tgt in "${tgt_langs_csv[@]}"; do
        tgt="$(echo "$tgt" | xargs)"
        [[ -z "$tgt" ]] && continue
        if [[ "$src" == "$tgt" ]]; then
          continue
        fi
        pair_file="$SEED_DIR/${src}_to_${tgt}.txt"
        raw_text_inputs+=("$pair_file")
      done
    done
    for extra in "${subset_text_inputs[@]}"; do
      [[ -z "$extra" ]] && continue
      raw_text_inputs+=("$extra")
    done

    dedup_text_inputs=()
    declare -A seen_text_inputs=()
    for text_in in "${raw_text_inputs[@]}"; do
      if [[ -f "$text_in" ]] && [[ -z "${seen_text_inputs[$text_in]+x}" ]]; then
        dedup_text_inputs+=("$text_in")
        seen_text_inputs["$text_in"]=1
      fi
    done
    pair_text_inputs_existing=()
    for pair_in in "${pair_text_inputs[@]}"; do
      if [[ -f "$pair_in" ]]; then
        pair_text_inputs_existing+=("$pair_in")
      fi
    done
    if [[ ${#dedup_text_inputs[@]} -eq 0 && ${#pair_text_inputs_existing[@]} -eq 0 ]]; then
      echo "[subset] no usable subset input files found"
      exit 1
    fi

    subset_text_builder_cmd=(
      "$PYTHON_BIN" "$SUBSET_TEXT_BUILDER"
      --out "$subset_text_file"
      --source-langs "$SOURCE_LANGS"
      --target-langs "$TARGET_LANGS"
      --min-text-chars "$SUBSET_MIN_TEXT_CHARS"
    )
    for pair_in in "${pair_text_inputs_existing[@]}"; do
      if [[ -f "$pair_in" ]]; then
        subset_text_builder_cmd+=(--pair-jsonl "$pair_in")
      fi
    done
    for text_in in "${dedup_text_inputs[@]}"; do
      subset_text_builder_cmd+=(--text "$text_in")
    done

    echo "+ ${subset_text_builder_cmd[*]}"
    if [[ "$DRY_RUN" == "1" ]]; then
      :
    else
      "${subset_text_builder_cmd[@]}"
    fi

    subset_cmd=(
      "$PYTHON_BIN" tools/vocab_subset.py
      --model "$SUBSET_MODEL"
      --text "$subset_text_file"
      --out "$VOCAB_SUBSET_DIR"
      --top-k "$SUBSET_TOP_K"
      --min-count "$SUBSET_MIN_COUNT"
      --dtype "$SUBSET_DTYPE"
    )
    if [[ -n "${SUBSET_MAX_LINES}" && "$SUBSET_MAX_LINES" != "0" ]]; then
      subset_cmd+=(--max-lines "$SUBSET_MAX_LINES")
    fi
    if [[ "$SUBSET_FILL_TO_TOP_K" == "1" ]]; then
      subset_cmd+=(--fill-to-top-k --fill-strategy "$SUBSET_FILL_STRATEGY")
    fi
    if [[ "$SUBSET_WRITE_CHECKPOINT" == "1" ]]; then
      subset_cmd+=(--write-checkpoint)
    fi
    if [[ "$SUBSET_ALSO_PRUNE_OUTPUT" == "1" ]]; then
      subset_cmd+=(--also-prune-output)
    fi
    if [[ "$SUBSET_FOR_CAUSAL_LM" == "1" ]]; then
      subset_cmd+=(--for-causal-lm)
    fi
    if [[ "$SUBSET_ALLOW_DOWNLOAD" == "1" ]]; then
      subset_cmd+=(--allow-download)
    fi

    echo "+ ${subset_cmd[*]}"
    if [[ "$DRY_RUN" == "1" ]]; then
      :
    else
      "${subset_cmd[@]}"
    fi
  fi
else
  if [[ -z "$VOCAB_SUBSET_DIR" && -d "$OUT_ROOT/$RUN_NAME/vocab_subset" ]]; then
    VOCAB_SUBSET_DIR="$OUT_ROOT/$RUN_NAME/vocab_subset"
  fi
fi

if has_subset_artifacts "$VOCAB_SUBSET_DIR"; then
  EFFECTIVE_STUDENT_MODEL="$VOCAB_SUBSET_DIR"
fi

if [[ "$SKIP_TRAIN" == "0" ]]; then
  cmd=(
    "$PYTHON_BIN" "$TRAINER"
    --pairs "$TRAIN_PAIRS_PATH"
    --teacher-model "$TEACHER_MODEL"
    --student-model "$EFFECTIVE_STUDENT_MODEL"
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
    --dtype "$DTYPE"
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
  if [[ -n "$VOCAB_SUBSET_DIR" ]]; then
    cmd+=(--vocab-subset-dir "$VOCAB_SUBSET_DIR")
    if [[ -z "$TOKENIZER_MODEL" ]]; then
      cmd+=(--tokenizer-model "$SUBSET_MODEL")
    else
      cmd+=(--tokenizer-model "$TOKENIZER_MODEL")
    fi
  fi

  if [[ "$ALLOW_DOWNLOAD" == "1" ]]; then
    cmd+=(--allow-download)
  fi

  run_training_cmd() {
    local -a args=("$@")
    echo "+ ${args[*]}"
    if [[ "$DRY_RUN" == "1" ]]; then
      return 0
    fi
    "${args[@]}"
  }

  if [[ "$AUTO_FALLBACK_TO_CPU" == "1" && "$DEVICE" != "cpu" ]]; then
    if ! run_training_cmd "${cmd[@]}"; then
      echo "Training on device '$DEVICE' failed. Retrying on cpu."
      cmd_cpu=("${cmd[@]}")
      for i in "${!cmd_cpu[@]}"; do
        if [[ "${cmd_cpu[$i]}" == "--device" ]]; then
          cmd_cpu[$((i + 1))]="cpu"
          break
        fi
      done
      run_training_cmd "${cmd_cpu[@]}"
    fi
  else
    run_training_cmd "${cmd[@]}"
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
  if [[ -n "$VOCAB_SUBSET_DIR" ]]; then
    eval_cmd+=(--vocab-subset-dir "$VOCAB_SUBSET_DIR")
    if [[ -z "$TOKENIZER_MODEL" ]]; then
      eval_cmd+=(--tokenizer-model "$SUBSET_MODEL")
    else
      eval_cmd+=(--tokenizer-model "$TOKENIZER_MODEL")
    fi
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
