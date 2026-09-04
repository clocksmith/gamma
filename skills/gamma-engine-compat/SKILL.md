---
name: gamma-engine-compat
description: Validate one user-selected Gamma engine/model/device lane, or compare explicitly supplied candidates against declared capability requirements.
---

# Gamma Engine Compatibility Validation

## Prerequisites

- Supply the workload mode and either one selected lane or a finite candidate list.
- State required capabilities such as raw logits, attention access, KV cache, or
  translation, plus permitted fallback behavior.
- Run from the Gamma repository root.

## Procedure

1. Inspect hardware and installed model/engine availability:

   ```bash
   PY=.venv/bin/python; [ -x "$PY" ] || PY=python3
   "$PY" tools/test_gpu_setup.py
   "$PY" gamma.py benchmark --list-models
   ```

2. For logits-dependent modes, validate candidates explicitly:

   ```bash
   "$PY" skills/gamma-engine-compat/scripts/check_specs.py --require-logits <engine:model>...
   ```

3. Run a minimal smoke for each supplied lane and record actual engine, device, model
   revision, output capability, and fallback state.
4. If selection was requested, apply only the user's stated criteria; otherwise report
   compatible lanes without choosing one.

## Validation

A lane passes only when the smoke exits successfully, exposes every required capability,
uses the declared device and model revision, and performs no undeclared fallback.

## Stop Conditions

Stop selection when criteria conflict or are incomplete. Stop on missing model identity,
failed device compute, or undeclared fallback. Do not download models or choose based on
unstated preferences.

## Outputs

A per-lane compatibility table, smoke commands/results, failure reasons, and—only when
requested with criteria—the selected lane.

## Side Effects

Runs local capability and model smokes. It does not install engines, download weights,
change defaults, or launch training.
