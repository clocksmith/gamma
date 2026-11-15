#!/usr/bin/env bash
set -euo pipefail
cd /Users/xyz/deco/gamma
GAIN_DIR=projects/distillation/wgsl/channel_gain
REMOTE_DIR=/home/x/deco/gamma/.work/channel-gain-20261112
RESTORED=.work/channel-gain-restored-04
# Read-only waiting; the fixed GPU workload is already running independently.
while ! ssh jupiter "python3 -c 'import json,pathlib; p=pathlib.Path(\"$REMOTE_DIR/$GAIN_DIR/native-confirmation-04/confirmation-receipt.json\"); r=json.load(p.open()) if p.exists() else {}; raise SystemExit(0 if r.get(\"status\")==\"confirmation_executed\" else 1)'" 2>/dev/null; do
  sleep 30
done
ssh jupiter "cd '$REMOTE_DIR' && python3 '$GAIN_DIR/archive_native_run.py' archive --selection-dir '$GAIN_DIR/native-selection-04' --confirmation-dir '$GAIN_DIR/native-confirmation-04' --output '$GAIN_DIR/archive-04'"
scp -r "jupiter:$REMOTE_DIR/$GAIN_DIR/archive-04" "$GAIN_DIR/archive-04"
python3 "$GAIN_DIR/archive_native_run.py" restore --archive "$GAIN_DIR/archive-04" --output "$RESTORED"
node "$GAIN_DIR/assemble_confirmation_evidence.mjs" \
  --protocol "$GAIN_DIR/protocol.json" --manifest "$GAIN_DIR/corpus-v1/manifest.json" \
  --selection "$RESTORED/selection/selection-receipt.json" \
  --confirmation "$RESTORED/confirmation/confirmation-receipt.json" \
  --runtime-lock "$GAIN_DIR/native-runtime-lock-03.json" \
  --stage-lock "$GAIN_DIR/native-stage-lock-04.json" \
  --continuation "$GAIN_DIR/protocol-continuation-02.json" \
  --budget "$GAIN_DIR/selection-budget-receipt.json" \
  --journal "$RESTORED/confirmation/confirmation.jsonl" \
  --output "$GAIN_DIR/confirmation-evidence-04.json"
python3 -m projects.distillation.wgsl.channel_gain.report_confirmation \
  --protocol "$GAIN_DIR/protocol.json" --evidence "$GAIN_DIR/confirmation-evidence-04.json" \
  --environment "$GAIN_DIR/environment-04.jsonl" \
  --json-output "$GAIN_DIR/confirmation-results-04.json" \
  --markdown-output "$GAIN_DIR/CONFIRMATION-RESULTS-04.md"
