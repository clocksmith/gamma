---
name: gamma-debug
description: Diagnose and fix Gamma engine, token-game, Mind Meld, benchmark, comparison, distillation, checkpoint, evaluation, reporting, and live training failures. Use when commands, logits, devices, runs, artifacts, metrics, or SAME-R evidence differ from their declared contract.
---

# Gamma Debugging

## Route To Existing Skills

- Training and checkpoint pipelines: `gamma-distillation`
- Runtime/model/device compatibility: `gamma-engine-compat`
- Benchmarks and reports: `gamma-benchmarking`
- Code generation studies: `gamma-codegen-ladder`
- Mind Meld: `gamma-mind-meld-ops`

Use this skill to connect those surfaces or diagnose repository-wide failures.

## Capture The Run Contract

Record Python executable, dependency imports, engine, model revision, device,
runtime mode, dataset and order hashes, resume checkpoint/stage, decode policy,
evaluator, process owner, log path, output directory, and receipt.

## Trace Maps

- Engine: CLI config -> factory -> backend capability -> logits/output
- Training: rows -> order -> trainer -> metrics stream -> checkpoint -> export
- Resume: checkpoint files -> trainer state -> declared resume stage -> next step
- Evaluation: checkpoint -> decoder -> predictions -> parser -> metric rows
- Reporting: raw artifacts -> manifest -> rebuild -> scoreboard -> register
- SAME-R: frozen contract -> lane -> control -> selection -> confirmation -> receipt

## Fix And Prove

Block environment drift, unsupported logits wrappers, ROCm visibility without
compute, tokenizer/vocabulary mismatch, and resume-stage mismatch. Patch the
first owner that violates the run contract.

Run the focused pytest file and syntax/import checks. For live training, verify
growing metrics, step logs, process ownership, and GPU activity. For reporting,
rebuild from raw artifacts and verify hashes instead of editing scoreboards.
