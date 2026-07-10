# Savant Student Status

Generated: 2026-07-07
Updated: 2026-07-10 UTC

## Target

Distill `google/translategemma-4b-it` into the Gemma 3 1B student for EN<->ES
with better external generalization than the current frozen best-5 mainline.

## Strict Student-Beats-Teacher Proof

Claim state: **pass**, scoped to the 128-row in-domain clean holdout.

Fresh paired greedy evaluation on the same ordered rows and ROCm runtime:

| scope | model | BLEU | chrF | samples |
| --- | --- | ---: | ---: | ---: |
| in-domain clean | Savant Gemma 3 1B | 54.4500 | 72.3516 | 128 |
| in-domain clean | TranslateGemma 4B | 45.4563 | 70.8387 | 128 |
| in-domain clean | student delta | +8.9937 | +1.5129 | 128 |

Direction checks also pass both metrics:

| direction | student BLEU | teacher BLEU | student chrF | teacher chrF |
| --- | ---: | ---: | ---: | ---: |
| EN->ES | 57.7884 | 51.3369 | 73.0159 | 72.9659 |
| ES->EN | 50.3034 | 37.7406 | 71.5408 | 68.2184 |

Receipt:
`projects/distillation/translation/runs/savant_student_teacher_paired_20260710/claim_receipt.md`

Boundary: this does not claim an external WMT13 sweep. The same fresh paired
external run scores the student at `33.7353 / 59.6065` and the teacher at
`33.6973 / 60.8011`, for deltas of `+0.0380 BLEU / -1.1946 chrF`.

## Native-Prompt KD Follow-Up

The trainer now encodes teacher batches with TranslateGemma's own tokenizer and
chat template, then aligns matching target-token positions before computing
KL. Historical Stage B used the student's prompt positions for both models.

New external Pareto candidates from the corrected KD lane:

| candidate | BLEU | chrF | result |
| --- | ---: | ---: | --- |
| ES->EN native-KD checkpoint 100 | 33.8753 | 59.7127 | new BLEU leader; improves both old metrics |
| balanced native-KD checkpoint 100 | 33.8237 | 59.7999 | new chrF leader; improves both old metrics |

Neither candidate clears external teacher chrF. Direct News Commentary SFT and
beam-4 decoding were evaluated and rejected because both reduced external BLEU
and chrF. The News Commentary builder pins dataset revision
`bbaf548083e788e0e6d2ca68efc325283fe2aff5`, excludes exact and high-overlap
eval matches, and marks the unknown-license output local-research-only.

## Current Artifact-Backed Proof Checkpoint

New best local student:

```text
projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1600_bf16_codexreplace05_pack06_defer_studentonly_v1/stage_a/checkpoint-004000
```

Scores:

| eval | BLEU | chrF | samples |
| --- | ---: | ---: | ---: |
| external WMT13 | 33.7353 | 59.6065 | 128 |
| in-domain clean | 54.4500 | 72.3516 | 128 |

Previous artifact-backed external student leader:

```text
projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1568_bf16_codexlow_pack06_prune10_defer_studentonly_v2/stage_a/checkpoint-003000
```

Previous score: external BLEU `32.9055`, chrF `59.4631`.

Latest completed follow-up:

```text
gamma-codexreplace05-pack06-ckpt4000-lr5e6-1k-dense250-v1.service (stopped, success)
projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1600_bf16_codexreplace05_pack06_ckpt4000_lr5e6_1k_dense250_v1
```

Input:

```text
projects/distillation/translation/training_data/frozen_best5_refine/frozen_best5.p05/pack_06/frozen_best5.pack_06.replace05.jsonl
```

Result: low-LR polish initialized from the new `33.7353` checkpoint did not
improve external generalization. Best polish checkpoint was `checkpoint-000250`
with external BLEU `33.6283`, chrF `59.6061`, and in-domain BLEU `54.2064`,
chrF `72.2358`.

Recent successful leader:

```text
gamma-codexreplace05-pack06-defer-studentonly-v1.service (stopped, success)
projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1600_bf16_codexreplace05_pack06_defer_studentonly_v1
```

Input:

```text
projects/distillation/translation/training_data/frozen_best5_refine/frozen_best5.p05/pack_06/frozen_best5.pack_06.replace05.jsonl
```

Result: `checkpoint-004000` is the current artifact-backed local student
leader with external BLEU `33.7353`, chrF `59.6065`, and in-domain BLEU
`54.4500`, chrF `72.3516`.

Recent completed non-leaders:

- `codexprune05_pack06_defer_studentonly_v1`: best external BLEU `32.8755`,
  chrF `58.9218` at `checkpoint-003500`; close to the previous `32.9055`
  leader but not a replacement.
- `codexreplace05_pack06_6k_dense500_defer_studentonly_v1`: best external BLEU
  `33.2481`, chrF `59.4567` at `checkpoint-003000`; confirms the longer
  schedule is weaker than the 4k `replace05` run for external WMT13.

Recent miss:

```text
gamma-codexseed7-pack06-prune10-defer-studentonly-v1.service (stopped, success)
projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1568_bf16_codexseed7_pack06_prune10_defer_studentonly_v1
```

Best checkpoint: `checkpoint-004000`, external BLEU `31.8697`, chrF `58.7989`.
This seed-only rerun did not clear the external BLEU `32` target.

## Implemented

- CLI judge filter:
  `projects/distillation/translation/pipeline/filter_translation_pairs_with_cli_judge.py`
- Codex/GEPA-style recipe tournament:
  `projects/distillation/translation/pipeline/run_cli_judge_tournament.py`
- Stage A launcher now forwards `--allow-download` to the trainer when online
  Hugging Face model fetches are required:
  `projects/distillation/translation/pipeline/run_stage_a_gold_shard_grid.py`
- Stage A launcher also supports `--student-only-sweep` so checkpoint ranking
  can run without blocking on 4B teacher comparison.
- Stage A launcher supports `--defer-live-sweeps`; this keeps training and
  checkpoint scoring separated and then sweeps all ready checkpoints after the
  trainer exits.
- Stage A launcher defaults now use Hugging Face model IDs
  (`google/translategemma-4b-it`, `google/gemma-3-1b-it`) instead of stale
  local snapshot paths.
- Codex sample tournament artifacts:
  `projects/distillation/translation/training_data/cli_judge_tournament/pack04_replace10_codex_lowfruit/`
- Full-candidate dataset QA:
  `projects/distillation/translation/training_data/qa/frozen_best5_refine_full_candidates.*`
- Random-candidate dataset QA:
  `projects/distillation/translation/training_data/qa/frozen_best5_refine_random_candidates.*`

## Low-Hanging Full Dataset Candidate

The full candidate scorer ranks these complete datasets:

| rank | dataset | rows | overall | external_match | gold_similarity | indomain_match |
| ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | `frozen_best5.pack_06.replace10.jsonl` | 1600 | 81.7402 | 54.5268 | 72.0613 | 44.9032 |
| 2 | `frozen_best5.pack_04.replace10.jsonl` | 1600 | 81.6783 | 54.5385 | 71.7414 | 44.9256 |
| 3 | `frozen_best5.pack_06.prune10.jsonl` | 1568 | 81.6207 | 54.5614 | 71.3423 | 44.8806 |
| 4 | `frozen_best5.pack_04.prune10.jsonl` | 1568 | 81.5576 | 54.5739 | 71.0154 | 44.9040 |

Selected low-hanging Stage A candidate:

```text
projects/distillation/translation/training_data/frozen_best5_refine/frozen_best5.p10/pack_06/frozen_best5.pack_06.replace10.compat.jsonl
```

Rationale: best overall full-dataset QA score, complete 1600-row replacement
variant, and old queue logs show this was previously considered first in the
row-refinement lane. Use the `.compat.jsonl` file for training because the raw
file omits the trainer's compatibility aliases: `lang`, `query`, `pos`, `neg`.

## Codex Sample Tournament

Sampled input:

```text
projects/distillation/translation/training_data/frozen_best5_refine/frozen_best5.p10/pack_04/frozen_best5.pack_04.replace10.jsonl
```

Sample rows: 8

Result:

- `entity_guard`: 8 keep, 0 drop, 0 review; champion by tournament weighting
- `strict_literal`: 8 keep, 0 drop, 0 review
- `external_wmt`: 2 keep, 6 drop, 0 review

Interpretation: entity preservation is a useful low-friction judge recipe;
external-style filtering is much stricter and should be used on a larger audit
pass before it becomes a training dataset.

## Launch Gate And Runtime

Do not launch GPU training until the compute probe succeeds in the same runtime
mode used by the run.

Historical host probes:

- `.venv/bin/python`: fails importing `torch`
- system `python3`: imports CUDA torch, but `torch.cuda.is_available()` is false
- `.venv_rocm` with `torch 2.9.1+rocm6.3`: sees AMD Radeon 8060S, matmul fails
  with `HIP error: no kernel image is available` or `invalid device function`
- `.venv_rocm` with `torch 2.9.1+rocm6.4`: sees AMD Radeon 8060S, matmul fails
  with `HIP error: no kernel image is available` or `invalid device function`
- `.venv_rocm` with `torch 2.10.0+rocm7.0`: sees AMD Radeon 8060S, matmul
  segfaults with no override, `HSA_OVERRIDE_GFX_VERSION=11.0.0`, and
  `HSA_OVERRIDE_GFX_VERSION=11.5.1`
- `.venv_rocm` with `torch 2.12.1+rocm7.2`: passes import, device discovery,
  and CUDA matmul with no HSA override.

Current working runtime:

- Python: `.venv_rocm/bin/python`
- Torch: `2.12.1+rocm7.2`
- Transformers: `4.57.6`
- HIP: `7.2.53211`
- Device: `Radeon 8060S Graphics`
- Runtime mode: normal ROCm, no `HSA_OVERRIDE_GFX_VERSION`

`rocm-smi` reports:

```text
Driver version: 7.0.0-22-generic
Card Series: Radeon 8060S Graphics
GFX Version: gfx1151
```

`rocminfo` reports:

```text
Name: gfx1151
ISA: amdgcn-amd-amdhsa--gfx1151
ISA: amdgcn-amd-amdhsa--gfx11-generic
```

## Launch Attempts

- `codexlow_pack06_replace10_v1`: failed because the raw dataset omitted
  `lang/query/pos/neg`.
- `codexlow_pack06_replace10c_v1`: failed because the launcher defaulted to
  stale local Hugging Face snapshot paths.
- `codexlow_pack06_replace10c_hf_v1`: failed because the trainer defaults to
  local-cache-only model loading.
- `codexlow_pack06_replace10c_hfdl_v1`: failed because the default Hugging Face
  cache contains symlinks to an absent `/run/media/x/models` mount.
- `codexlow_pack06_replace10c_hfcache_v1`: failed because the isolated
  Hugging Face cache did not yet contain the token.
- `codexlow_pack06_replace10c_hfcacheauth_v1`: completed Stage A training and
  wrote `final`, but the automated teacher-compare sweep was stopped after
  repeated teacher-tokenizer crashes.

The completed run uses:

```text
HF_HOME=/home/x/.cache/huggingface_gamma_rocm
HF_HUB_CACHE=/home/x/.cache/huggingface_gamma_rocm/hub
```

The original `~/.cache/huggingface/hub` layout was not changed; it still has
model repo symlinks that expect `/run/media/x/models` to be mounted.

## Probe Command

Run this before launching:

```bash
.venv_rocm/bin/python - <<'PY'
import torch
print("cuda_available", torch.cuda.is_available())
print("cuda_device_count", torch.cuda.device_count())
a = torch.randn((128, 128), device="cuda")
b = torch.randn((128, 128), device="cuda")
c = (a @ b).float().mean().item()
torch.cuda.synchronize()
print("cuda_matmul_ok", c)
PY
```

## Completed Stage A Run

Systemd unit:

```text
gamma-codexlow-pack06-replace10c-hfcacheauth-v1.service (stopped)
```

Run root:

```text
projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1600_bf16_codexlow_pack06_replace10c_hfcacheauth_v1
```

Logs:

```text
projects/distillation/translation/runs/codexlow_pack06_replace10c_hfcacheauth_v1.systemd.log
projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1600_bf16_codexlow_pack06_replace10c_hfcacheauth_v1/logs/stage_a_gold_grid_train.log
projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1600_bf16_codexlow_pack06_replace10c_hfcacheauth_v1/stage_a/metrics.jsonl
```

Confirmed training completion:

```text
[A_then_B_stage_a] step=4000 loss=0.1457 ce=0.1457 kd=0.0000 tri=0.0000 lr=0.0
```

Selected final:

```text
projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1600_bf16_codexlow_pack06_replace10c_hfcacheauth_v1/final
```

Student-only final eval, without teacher compare:

| eval | BLEU | chrF | samples |
| --- | ---: | ---: | ---: |
| external WMT13 | 32.6083 | 58.6464 | 128 |
| in-domain clean | 53.9959 | 72.0120 | 128 |

Best comparable historical rows found in existing scoreboards:

| eval | run/checkpoint | BLEU | chrF |
| --- | --- | ---: | ---: |
| external WMT13 | `rows2240_bf16_confirm_best7/checkpoint-002000` | 32.8224 | 59.4068 |
| in-domain clean | `rows1920_bf16_20260310T224540/checkpoint-002000` | 56.2174 | 72.9556 |

Conclusion: this produced a valid trained student, but it is not better than the
best existing student by the current BLEU/chrF validation scoreboards.

## Completed Blend Run

Purpose: preserve the external score from `pack_06.replace10` while anchoring
with high-quality rebucketed pack 08.

Code fix applied before launch:

- `projects/distillation/translation/pipeline/run_stage_a_gold_shard_grid.py`
  now forwards `--allow-download` to `run_stage_b_checkpoint_sweep.py`, so
  teacher compare evals do not silently fall back to local-cache-only loading.
- The same wrapper now supports `--student-only-sweep` for future runs. This
  completed run was trained before that flag existed, so the teacher sweep was
  stopped after training finished and a separate student-only checkpoint sweep
  was run.

Systemd unit:

```text
gamma-codexblend-pack06r10-pack08-v1.service (stopped after training completion)
```

Run root:

```text
projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_codexblend_pack06r10_pack08_v1
```

Input contract:

```text
merge_jsonl(
  projects/distillation/translation/training_data/frozen_best5_refine/frozen_best5.p10/pack_06/frozen_best5.pack_06.replace10.compat.jsonl,
  projects/distillation/translation/training_data/gold_shards_rebucketed/gold_rebucketed_320.pack_08.q97_3716.rows320.jsonl
)
```

Runtime:

```text
python=.venv_rocm/bin/python
torch=2.12.1+rocm7.2
runtime_mode=normal_rocm
HF_HOME=/home/x/.cache/huggingface_gamma_rocm
```

Confirmed active:

```text
[A_then_B_stage_a] step=4000 loss=0.0417 ce=0.0417 kd=0.0000 tri=0.0000 lr=0.0
```

Trainer-selected checkpoint by loss:

```text
projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_codexblend_pack06r10_pack08_v1/stage_a/checkpoint-004000
```

Student-only checkpoint sweep:

```text
projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_codexblend_pack06r10_pack08_v1/stage_a_checkpoint_sweep_greedy_studentonly/
```

Checkpoint ranking:

| checkpoint | avg BLEU | avg chrF | external BLEU | external chrF | in-domain BLEU | in-domain chrF |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `checkpoint-004000` | 42.8843 | 65.9531 | 31.6237 | 58.6982 | 54.1449 | 73.2081 |
| `checkpoint-002000` | 42.5377 | 65.5767 | 32.2180 | 58.7093 | 52.8574 | 72.4442 |
| `checkpoint-003000` | 42.5251 | 65.8250 | 31.5986 | 58.6758 | 53.4517 | 72.9742 |
| `checkpoint-001000` | 39.8837 | 63.8845 | 30.5462 | 57.6860 | 49.2213 | 70.0831 |

Best result from this run by target:

| target | checkpoint | BLEU | chrF |
| --- | --- | ---: | ---: |
| external WMT13 | `checkpoint-002000` | 32.2180 | 58.7093 |
| in-domain clean | `checkpoint-004000` | 54.1449 | 73.2081 |

Comparison to the best comparable historical rows already in the local
scoreboards:

| eval | previous best | this blend best | result |
| --- | ---: | ---: | --- |
| external WMT13 BLEU | 32.8224 | 32.2180 | not better |
| external WMT13 chrF | 59.4068 | 58.7093 | not better |
| in-domain BLEU | 56.2174 | 54.1449 | not better |
| in-domain chrF | 72.9556 | 73.2081 | new high in this comparable Stage A set |

Conclusion: the blend still does not produce the savant external student, but
it does improve in-domain chrF within the comparable Stage A gold-grid rows used
for this decision. The low-hanging next move is to keep the external-winning
checkpoint lane separate from the in-domain anchor lane instead of averaging
them into one four-checkpoint training curve.

## Completed External Candidate: pack04 random10

Run root:

```text
projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1568_bf16_codexlow_pack04_random10_defer_studentonly_v1
```

Input:

```text
projects/distillation/translation/training_data/frozen_best5_refine/frozen_best5.p10/pack_04/frozen_best5.pack_04.random10.jsonl
```

Contract:

```text
schedule=A_then_B
runtime_mode=normal_rocm
sweep_mode=after_train
sweep=student_only
```

Student-only checkpoint sweep:

| checkpoint | avg BLEU | avg chrF | external BLEU | external chrF | in-domain BLEU | in-domain chrF |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `checkpoint-002000` | 43.9764 | 65.7881 | 32.0233 | 58.5229 | 55.9294 | 73.0533 |
| `checkpoint-003000` | 43.8553 | 65.9874 | 32.1481 | 58.7076 | 55.5626 | 73.2671 |
| `checkpoint-004000` | 43.8534 | 66.0290 | 32.3030 | 58.9223 | 55.4039 | 73.1358 |
| `checkpoint-001000` | 42.2463 | 65.0635 | 30.8410 | 58.3600 | 53.6515 | 71.7670 |

Conclusion: not the external breakthrough. It improves the comparable Stage A
in-domain lane, but its best external score is still below
`rows2240_bf16_confirm_best7/checkpoint-002000`.

## Completed External Candidate: pack04 replace10

Systemd unit:

```text
gamma-codexlow-pack04-replace10-defer-studentonly-v1.service (stopped)
```

Run root:

```text
projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1600_bf16_codexlow_pack04_replace10_defer_studentonly_v1
```

Input:

```text
projects/distillation/translation/training_data/frozen_best5_refine/frozen_best5.p10/pack_04/frozen_best5.pack_04.replace10.jsonl
```

Contract:

```text
[run-contract] run_name=translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1600_bf16_codexlow_pack04_replace10_defer_studentonly_v1 pairs_input_spec=/home/x/deco/gamma/projects/distillation/translation/training_data/frozen_best5_refine/frozen_best5.p10/pack_04/frozen_best5.pack_04.replace10.jsonl resume_from=none resume_stage=none decode=greedy eval_dataset_paths=/home/x/deco/gamma/projects/distillation/translation/training_data/translate_distill_pairs.eval2_wmt13_enes_128.jsonl,/home/x/deco/gamma/projects/distillation/translation/training_data/translate_distill_pairs.eval3_indomain_clean_merged_128.jsonl device=cuda schedule=A_then_B runtime_mode=normal_rocm sweep_mode=after_train
```

Student-only checkpoint sweep:

| checkpoint | avg BLEU | avg chrF | external BLEU | external chrF | in-domain BLEU | in-domain chrF |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `checkpoint-004000` | 43.3114 | 65.5202 | 32.5811 | 58.9875 | 54.0417 | 72.0529 |
| `checkpoint-003000` | 43.0721 | 65.5461 | 32.2489 | 58.9322 | 53.8952 | 72.1599 |
| `checkpoint-002000` | 42.5935 | 65.1611 | 31.8522 | 58.6638 | 53.3348 | 71.6585 |
| `checkpoint-001000` | 42.1849 | 64.1236 | 30.8992 | 57.0933 | 53.4706 | 71.1539 |

The launcher normalized the raw rows into:

```text
projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1600_bf16_codexlow_pack04_replace10_defer_studentonly_v1/inputs/train_pairs.rows1600.normalized.jsonl
```

Conclusion: not the external breakthrough. Its best external checkpoint is
below `pack06_prune10_defer_studentonly_v2/checkpoint-003000`.

Reporting refresh:

```text
run_rows=88 eval_rows=267 compare_rows=139
```

## Completed Polish Candidate: pack06 prune10 checkpoint-003000

Purpose: initialize from the current best local 1B student and run a
1000-step lower-LR Stage A polish pass over the winning `pack_06.prune10`
training set.

Systemd unit:

```text
gamma-codexpolish-pack06-prune10-ckpt3000-lr5e6-v1.service (stopped)
```

Run root:

```text
projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1568_bf16_codexpolish_pack06_prune10_ckpt3000_lr5e6_v1
```

Student initializer:

```text
projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1568_bf16_codexlow_pack06_prune10_defer_studentonly_v2/stage_a/checkpoint-003000
```

Input:

```text
projects/distillation/translation/training_data/frozen_best5_refine/frozen_best5.p10/pack_06/frozen_best5.pack_06.prune10.jsonl
```

Contract:

```text
[run-contract] run_name=translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1568_bf16_codexpolish_pack06_prune10_ckpt3000_lr5e6_v1 pairs_input_spec=/home/x/deco/gamma/projects/distillation/translation/training_data/frozen_best5_refine/frozen_best5.p10/pack_06/frozen_best5.pack_06.prune10.jsonl resume_from=none resume_stage=none decode=greedy eval_dataset_paths=/home/x/deco/gamma/projects/distillation/translation/training_data/translate_distill_pairs.eval2_wmt13_enes_128.jsonl,/home/x/deco/gamma/projects/distillation/translation/training_data/translate_distill_pairs.eval3_indomain_clean_merged_128.jsonl device=cuda schedule=A_then_B runtime_mode=normal_rocm sweep_mode=after_train
```

Preflight:

```text
python=/home/x/deco/gamma/.venv_rocm/bin/python
torch=2.12.1+rocm7.2
transformers=4.57.6
hip=7.2.53211
cuda_available=true
cuda_device_count=1
cuda_matmul_ok=true
```

Launch verification:

```text
[A_then_B_stage_a] step=20 loss=0.1046 ce=0.1046 kd=0.0000 tri=0.0000 lr=5.00e-06
```

Student-only checkpoint sweep:

| checkpoint | avg BLEU | avg chrF | external BLEU | external chrF | in-domain BLEU | in-domain chrF |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `checkpoint-001000` | 43.8653 | 66.1316 | 32.7147 | 59.3117 | 55.0160 | 72.9515 |
| `checkpoint-000250` | 43.6838 | 66.1240 | 32.5040 | 59.2697 | 54.8635 | 72.9783 |
| `checkpoint-000500` | 43.5446 | 66.0134 | 32.4609 | 59.2292 | 54.6283 | 72.7976 |
| `checkpoint-000750` | 43.5247 | 65.9187 | 32.5374 | 59.1869 | 54.5121 | 72.6505 |

Conclusion: the polish pass did not beat the current external champion. Its
best external checkpoint, `checkpoint-001000`, sits below
`pack06_prune10_defer_studentonly_v2/checkpoint-003000`.

Reporting refresh:

```text
run_rows=89 eval_rows=275 compare_rows=143
```

Launch command:

```bash
HF_HOME=/home/x/.cache/huggingface_gamma_rocm \
HF_HUB_CACHE=/home/x/.cache/huggingface_gamma_rocm/hub \
.venv_rocm/bin/python projects/distillation/translation/pipeline/run_stage_a_gold_shard_grid.py \
  --sizes 1568 \
  --dataset 1568=projects/distillation/translation/training_data/frozen_best5_refine/frozen_best5.p10/pack_06/frozen_best5.pack_06.prune10.jsonl \
  --tag codexpolish_pack06_prune10_ckpt3000_lr5e6_v1 \
  --python-bin .venv_rocm/bin/python \
  --teacher-model google/translategemma-4b-it \
  --student-model projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1568_bf16_codexlow_pack06_prune10_defer_studentonly_v2/stage_a/checkpoint-003000 \
  --allow-download \
  --total-steps 1000 \
  --sft-steps 1000 \
  --save-every 250 \
  --keep-checkpoints 4 \
  --batch-size 1 \
  --lr 5e-6 \
  --log-every 20 \
  --max-prompt-length 256 \
  --max-new-tokens 192 \
  --device cuda \
  --eval-device cuda \
  --dtype bfloat16 \
  --eval-dtype bfloat16 \
  --student-only-sweep \
  --defer-live-sweeps \
  --hsa-override-gfx-version= \
  --launch
```

## Completed Dense Checkpoint Confirmation: pack06 prune10 seed42

Purpose: rerun the current winning `pack_06.prune10` lane from the base 1B
student with checkpoints every 500 steps, so the sweep can test the region
around the previous 3000-step peak instead of only 1000-step intervals.

Systemd unit:

```text
gamma-codexdense-pack06-prune10-seed42-500ckpts-v1.service (stopped, success)
```

Run root:

```text
projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1568_bf16_codexdense_pack06_prune10_seed42_500ckpts_v1
```

Input:

```text
projects/distillation/translation/training_data/frozen_best5_refine/frozen_best5.p10/pack_06/frozen_best5.pack_06.prune10.jsonl
```

Contract:

```text
[run-contract] run_name=translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1568_bf16_codexdense_pack06_prune10_seed42_500ckpts_v1 pairs_input_spec=/home/x/deco/gamma/projects/distillation/translation/training_data/frozen_best5_refine/frozen_best5.p10/pack_06/frozen_best5.pack_06.prune10.jsonl resume_from=none resume_stage=none decode=greedy eval_dataset_paths=/home/x/deco/gamma/projects/distillation/translation/training_data/translate_distill_pairs.eval2_wmt13_enes_128.jsonl,/home/x/deco/gamma/projects/distillation/translation/training_data/translate_distill_pairs.eval3_indomain_clean_merged_128.jsonl device=cuda schedule=A_then_B runtime_mode=normal_rocm sweep_mode=after_train
```

Preflight:

```text
python=/home/x/deco/gamma/.venv_rocm/bin/python
torch=2.12.1+rocm7.2
transformers=4.57.6
hip=7.2.53211
cuda_available=true
cuda_device_count=1
cuda_matmul_ok=true
```

Result:

```text
checkpoint-003000: external BLEU 32.9055, chrF 59.4631; in-domain BLEU 54.8940, chrF 72.8595
```

Conclusion: denser 500-step checkpointing found the same peak as the
`codexlow_pack06_prune10_defer_studentonly_v2` run and did not uncover a
stronger adjacent checkpoint.
