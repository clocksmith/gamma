# Gamma reconciliation and recovered comparison on 128

Execution moved to verified `x@128`, using `/home/x/deco/gamma/.venv_rocm/bin/python`.
Component intent is preserved; no framework, security, model, vocabulary or
protected-evaluation boundary changed. All six existing SSH directions among
128, suby and macOS passed strict pinned ED25519 verification. See
[connectivity receipt](connectivity-verified.json).

## Code and evidence reconciliation

The 128 checkout fast-forwarded 50 commits from `06402b253` to `36404d2a1`.
No commit ancestry was rewritten. Eleven of its 15 dirty/untracked files already
matched upstream; three editor files had additive approved-library/comparison
support upstream, and the sandbox retained cancellation cleanup plus trustworthy
startup reporting. The older local versions remain separate in named stash
`bc9fac9d83894e6a1fac5c1c41375d7d8e342c63` and a hash-verified archive under the
Codex task's `preservation-128/`. They were not overwritten by a whole-workspace sync.

Suby's twelve-file diagnosis patch and four named raw development-evidence
folders were archived onto 128. Its negative-coordination parser fix remains an
unselected development candidate; its training preflight rejects truncated inputs.
Recognition defaults and prior failure evidence were not promoted or relabeled.
The raw recovered assets remain separate from suby's rebuilt corpus.

The original checkpoint `25f9ca2f...`, corpus `566d6b44...`, codec and nine exact
training source files were recovered and verified. All 18 raw predictions in this
comparison equal the historical student's predictions. Eleven historical artifact
bindings and all 62 completed-run artifact bindings pass. See
[reconciliation receipt](reconciliation.json) and [integrity checks](comparison-integrity.json).

## Actual solving result

The recovered checkpoint, original 18 development problems, original two-second
budget and one frozen correction policy were evaluated without training. All route
decisions were captured before independent tests were loaded.

| Route | Fit accepted correct | Audit accepted correct | Wrong accepted | Fit p95 | Audit p95 |
|---|---:|---:|---:|---:|---:|
| Raw | 4/10 | 0/8 | 0 | 1.975 s | 0.969 s |
| Bounded correction | 4/10 | 0/8 | 0 | 1.976 s | 1.094 s |
| Nearest fit graph | 8/10 | 0/8 | 0 | 1.972 s | 0.988 s |

Every route had zero infrastructure failures. Nearest fit had nine independently
correct fit programs, but only eight accepted within the decision contract. Raw
and corrected fit each abstained six times; nearest fit abstained twice; every
audit route abstained eight times. Maximum fit latency exceeded two seconds,
and those late cases abstained. Complete phase costs and fixed denominators are
in [summary.json](summary.json) and the [generated report](report.md).

Correction gained one structurally valid fit graph but no correct accepted answer:
zero useful or harmful corrections, one validity-only neutral change. The audit
correctness-gain gate failed; the candidate is rejected. This does not demonstrate
learned generalization or qualify protected/nearby-variant scoring.

The original encoder's 1,024-token truncation was deliberately preserved for this
historical comparison. Two fit-memory descriptions contain 1,565 and 1,660 tokens;
all request texts fit. This is not full-text memory qualification. Suby's separate
new training proposal still requires a declared full-text policy and owner approval.

## Scoring defect and transparent recovery

The first run `typed-composer-recovered-128-v1` captured all predictions and public
decisions, then refused independent scoring because `typed_scoring` hashed tests
with compact graph JSON, whereas pair qualification used standard sorted JSON.
The original tests matched all 18 qualification hashes; no test changed.

The scorer now uses the existing `mine.digest` convention for test authority and
mutation checks. Candidate/graph/receipt hash conventions remain unchanged.
Regression coverage rejects the wrong graph digest and preserves interrupted
receipt/mutation checks. The first failed run and its log remain intact.

A new evaluator identity, `typed-composer-recovered-128-scorefix-v1`, copied
captures, decisions, setup and sandbox probe byte-for-byte. The recovery checked
that only the exact reviewed scorer source edit differed; every other source,
runtime, configuration and asset binding matched. No inference or public decision
was repeated. [recovery.json](recovery.json) binds both candidate identities;
[recover_comparison_scoring.py](recover_comparison_scoring.py) records the exact
one-time migration, including rejection of previously scored outcomes.

The new candidate is `4621bbb95ad87d5db4d2251bd58c2bf6fde8005242550f359befa6157e650749`.
The scoring run completed all 54 route receipts. Measured capture-stage wall time
was 59.18 seconds and scoring-stage wall time 15.31 seconds. Capture maximum RSS
was 5,095,348 KiB; observed cgroup peak was 6,364,274,688 bytes, below 8 GiB.
Four existing Reploid participants remained active; no shared-host latency claim
is presented as an uncontended hardware benchmark.

## Software checks and remaining boundaries

Before evaluation: 78 focused tests and 58 subtests passed, including real Linux
sandbox checks. After the scorer fix: 23 focused tests and 11 subtests passed.
These sets overlap and are not additive solving evidence. Compressed logs retain
both successes and the actual failed first run.

1a/1b retain suby's bounded recognition findings and failed fresh ambiguity test;
the imported parser repair is not newly recognition-qualified. No consumed fresh
set was replayed. 2a now has the original matched comparison above. 2b still has
no independent nearby-variant result. Protected 66-target/60-family student
scoring and the autonomous graph-development loop remain closed.

Reproduce on 128 with offline assets and the preserved source/environment identity:

```sh
OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 \
TOKENIZERS_PARALLELISM=false HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
PYTHONPATH=projects/algorithm_solver .venv_rocm/bin/python \
  -m algsolve.synth.compare_typed \
  --name typed-composer-recovered-128-scorefix-v1 --resume-scoring
```

The generated report's generic `.venv` example is not the resolved 128 interpreter.
Raw files are ignored under the two named `runs/` directories; checkpoint/corpus
originals remain in their original paths. Source, aggregate evidence and metadata
are committed on main. GitHub auth from 128's existing empty agent failed; suby's
existing origin access is used for publication without credential changes.
