# CATSCAN: Per-layer MLP LoRA reconfiguration, v5 development diagnostics

Parent: [Request-specific reconfiguration experiments](../CATSCAN.md)

## Target

Find out, on development tasks only, why the sealed v4 closed-form per-layer LoRA lost every
multi-token answer, and test candidate compiler changes before a v5 protocol is locked.

## Authority

- Owns `projects/reconfiguration/query_swiglu_fastweight_v5_dev/` and the receipts in
  `.work/query-swiglu-fastweight-v5-dev/`.
- Reads the sealed v4 compiler, evaluator and task generator. It never edits them.

## Scope

- Development runs on seed 23017 tasks, with a base-model arm in every run.
- A copy of the v4 compiler carrying one candidate change at a time.
- Post-hoc audits of sealed v4 inputs that run no model and score nothing.

## Contracts

- Input: the sealed v4 files, locally provisioned Q4K models, a clean Doppler checkout.
- Output: development receipts that record the hashes of the code and model they used, and a
  README that labels every number exploratory.

## Invariants

- No file hashed in `protocol_v4.json` and no sealed receipt is modified.
- No arm is scored on a confirmation seed; the runner refuses any seed other than 23017.
- One WebGPU process at a time, started only after the GPU is confirmed free.

## Acceptance

- `anchor_audit.py` and `tally.py` reproduce the README's tables from the committed inputs
  and receipts.

## Non-goals

- Confirming any result, or downloading model weights that are not provisioned.

## Freedom

- Adding arms and candidate compiler changes, each as its own receipt.
