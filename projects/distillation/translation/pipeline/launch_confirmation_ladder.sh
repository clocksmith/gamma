#!/usr/bin/env bash
# Confirmation ladder: test multi-size shard compositions derived from
# the leave-two-out pack ranking analysis (28/28 complete).
#
# Runs sequentially on one GPU. Each run: ~4000 steps Stage A + checkpoint eval sweep.
# Settings match the leave-two-out sweep exactly.
#
# Compositions:
#   best-4: packs 01,02,03,06 (1280 rows) — predicted BLEU 32.15
#   best-5: packs 01,02,03,04,06 (1600 rows) — predicted BLEU 32.33
#   swap-6: packs 01,02,03,04,06,08 (1920 rows) — predicted BLEU 32.33
#   best-7: packs 01,02,03,04,05,06,08 (2240 rows) — predicted BLEU 32.34
#
# Note: best-6 (01,02,03,04,05,06) already observed at 32.46 via drop_07_08.

set -euo pipefail

cd /home/x/deco/gamma

PY=.venv/bin/python
GRID_SCRIPT=projects/distillation/translation/pipeline/run_stage_a_gold_shard_grid.py
PACKS=projects/distillation/translation/training_data/gold_shards_rebucketed

P01="$PACKS/gold_rebucketed_320.pack_01.q97_4484.rows320.jsonl"
P02="$PACKS/gold_rebucketed_320.pack_02.q97_1397.rows320.jsonl"
P03="$PACKS/gold_rebucketed_320.pack_03.q96_4352.rows320.jsonl"
P04="$PACKS/gold_rebucketed_320.pack_04.q96_3328.rows320.jsonl"
P05="$PACKS/gold_rebucketed_320.pack_05.q96_0642.rows320.jsonl"
P06="$PACKS/gold_rebucketed_320.pack_06.q95_9634.rows320.jsonl"
P08="$PACKS/gold_rebucketed_320.pack_08.q97_3716.rows320.jsonl"

COMMON_ARGS=(
  --total-steps 4000
  --sft-steps 4000
  --save-every 2000
  --keep-checkpoints 2
  --device cuda
  --dtype bfloat16
  --hsa-override-gfx-version 11.0.0
  --launch
)

echo "=== Confirmation Ladder: 4 runs ==="
echo "Started: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo ""

# --- best-4: packs 01,02,03,06 = 1280 rows ---
echo "[1/4] best-4: packs 01,02,03,06 (1280 rows)"
"$PY" "$GRID_SCRIPT" \
  --sizes 1280 \
  --dataset "1280=$P01,$P02,$P03,$P06" \
  --tag "confirm_best4" \
  "${COMMON_ARGS[@]}"
echo "[1/4] best-4 done: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo ""

# --- best-5: packs 01,02,03,04,06 = 1600 rows ---
echo "[2/4] best-5: packs 01,02,03,04,06 (1600 rows)"
"$PY" "$GRID_SCRIPT" \
  --sizes 1600 \
  --dataset "1600=$P01,$P02,$P03,$P04,$P06" \
  --tag "confirm_best5" \
  "${COMMON_ARGS[@]}"
echo "[2/4] best-5 done: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo ""

# --- swap-6: packs 01,02,03,04,06,08 = 1920 rows ---
echo "[3/4] swap-6: packs 01,02,03,04,06,08 (1920 rows)"
"$PY" "$GRID_SCRIPT" \
  --sizes 1920 \
  --dataset "1920=$P01,$P02,$P03,$P04,$P06,$P08" \
  --tag "confirm_swap6" \
  "${COMMON_ARGS[@]}"
echo "[3/4] swap-6 done: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo ""

# --- best-7: packs 01,02,03,04,05,06,08 = 2240 rows ---
echo "[4/4] best-7: packs 01,02,03,04,05,06,08 (2240 rows)"
"$PY" "$GRID_SCRIPT" \
  --sizes 2240 \
  --dataset "2240=$P01,$P02,$P03,$P04,$P05,$P06,$P08" \
  --tag "confirm_best7" \
  "${COMMON_ARGS[@]}"
echo "[4/4] best-7 done: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo ""

echo "=== Confirmation Ladder Complete ==="
echo "Finished: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo ""
echo "Next: rebuild results bundle and re-run pack effect analysis."
echo "  $PY projects/distillation/translation/pipeline/rebuild_translation_results_bundle.py"
echo "  $PY projects/distillation/translation/pipeline/analyze_pack_effects.py"
