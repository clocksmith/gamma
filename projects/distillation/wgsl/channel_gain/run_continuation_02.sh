#!/usr/bin/env bash
set -euo pipefail
# Run from the isolated Jupiter Gamma snapshot. The original freeze is retained;
# continuation02 changes the efficiency target's execution role, not its score.
GAIN_DIR=projects/distillation/wgsl/channel_gain
export PLAYWRIGHT_HOST_PLATFORM_OVERRIDE=ubuntu24.04-x64
export PLAYWRIGHT_BROWSERS_PATH=/home/x/deco/doppler/.work/channel-gain-20261112/browsers
COMMON=(
  --protocol "$GAIN_DIR/protocol.json"
  --freeze "$GAIN_DIR/protocol-freeze.json"
  --amendment "$GAIN_DIR/protocol-amendment-01.json"
  --budget "$GAIN_DIR/selection-budget-receipt.json"
  --config "$GAIN_DIR/native-jupiter-config.json"
  --corpus "$GAIN_DIR/corpus-v1"
  --runtime-lock "$GAIN_DIR/native-runtime-lock-03.json"
  --smoke "$GAIN_DIR/native-smoke-03.json"
  --replay "$GAIN_DIR/public-replay-03.json"
  --replay-seal "$GAIN_DIR/public-replay-03-seal.json"
  --device-options "$GAIN_DIR/public-replay-device-options.json"
  --continuation "$GAIN_DIR/protocol-continuation-02.json"
  --stage-lock "$GAIN_DIR/native-stage-lock-04.json"
  --gpu-authorized
)
node "$GAIN_DIR/native_experiment.mjs" --action selection "${COMMON[@]}" \
  --output-dir "$GAIN_DIR/native-selection-04"
# Confirmation validates complete selection and matching continuation; a partial
# selection cannot advance even if the preceding CLI returned a receipt.
node "$GAIN_DIR/native_experiment.mjs" --action confirmation "${COMMON[@]}" \
  --selection "$GAIN_DIR/native-selection-04/selection-receipt.json" \
  --output-dir "$GAIN_DIR/native-confirmation-04"
