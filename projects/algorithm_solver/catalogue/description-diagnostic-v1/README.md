# Public description ranking diagnostic v1

Prepared for integrator review **before any encoder run**. This directory is a
20-contract local experiment, not the missing historical/full-corpus index.
The denominator remains 4,081 known identities; the current source allowlist is
400. No source or cases are read. Contracts are the exact six public v1 and
fourteen accessible public v2 contracts, with raw-file hashes and official URLs.
The index projects only public constraints, result semantics and complexity;
local interface/effect policies and qualification still belong to KnownCatalogue.

`queries.json` freezes 20 independently written positive paraphrases, four
ambiguity controls and four controls absent **from this pilot**, not necessarily
absent from all 4,081. Authors saw the public contracts; these are not blinded or
held-out measurements. No model scores were observed while preparing them.
Queries omit some contractual details deliberately; a high rank cannot establish
complete semantic agreement. All queries retain unknown/outside interpretations.

`run_diagnostic.py` binds the index, queries, code, CPU encoder and v4 service
configuration by SHA-256. It uses the existing offline CPU adapter, two Torch
threads and one interop thread, batch two, 8 GiB virtual-memory/120-second soft
CPU limits, with an external 180-second wall limit required by the launch command.
No downloads, training, GPU, candidate execution or source materialization occur.
All20 rankings use cosine similarity with deterministic identity tie order, never
language availability. Top-three **candidate** metadata comes from the same
KnownCatalogue; it is never an accepted answer. Every query abstains. Any query
truncation suppresses its ranking and candidate metadata; any document truncation
suppresses these for every query. No scores, margins or thresholds are tuned or
reused from historical calibration.

Report positive rank hits and reciprocal-rank sum separately from serving:
accepted answers are zero and abstentions are 28 by design. Those abstentions
are policy, not a learned classifier or empirical precision result. Full1b
semantic/boundary/precision/population gates remain open. Reported first-call
timing includes loading and integrity checks; OS cache is uncontrolled, so it is
**not cold-cache latency**. No runtime result is claimed until a native receipt
exists.

## Review and native run

Review `index.json`, `queries.json`, `freeze.json` and runner source first. Frozen
bundle SHA-256 (`freeze.json`):
`347db7771b24ceb6e4e093ab2948ce2e571cb3ed32d3b6eb380b04b6cccb9f6d`.
The trusted operator supplies exact current v4 configuration and private model
root. Run only in the approved native dot terminal after CPU/UI coordination:

```sh
cd "$CHECKOUT"
PYTHONPATH="$CHECKOUT" timeout --signal=TERM --kill-after=5 180 \
  "$ENCODER_WORKSPACE/venv/bin/python" \
  projects/algorithm_solver/catalogue/description-diagnostic-v1/run_diagnostic.py \
  --freeze-sha256 347db7771b24ceb6e4e093ab2948ce2e571cb3ed32d3b6eb380b04b6cccb9f6d \
  --service-config "$TRUSTED_V4_CONFIG" \
  --model-root "$ENCODER_WORKSPACE/model" --output "$PRIVATE_RECEIPT"
```

Synthetic tests (no model import/execution):

```sh
python3 -m unittest discover \
  -s projects/algorithm_solver/catalogue/description-diagnostic-v1 -p 'test_*.py'
```

Five tests pass: stable ties, nonfinite rejection, top-one always abstains,
truncation suppresses metadata, absent control has no positive rank metric.
Metadata-only preflight resolves all20 exact IDs in the pinned v4 catalogue.

## Native result (reviewed freeze, no revision or tuning)

`NATIVE-AGGREGATE-RECEIPT-v1.json` records native exit zero: 19/20 positive
queries ranked first, 20/20 in the first three, mean reciprocal rank 0.975.
All28 requests abstained; no answers were accepted. None of the20 documents or
28 queries truncated. The four ambiguity and four absent-from-pilot controls
provide no semantic-classification accuracy claim: abstention was unconditional.
Total45.5743 seconds, first document encode30.5964 seconds, peak RSS3,836,884 KiB.
The first-call measurement is not cold OS cache. Raw rankings and candidate
metadata remain private, with their report hash in the aggregate receipt.
Frozen inputs and executed runner were preserved in private read-only snapshots.
No rerun, threshold change, source materialization, or scope expansion followed
these scores. This is a completed local ranking mechanism experiment, not1b
recognition qualification or an accepted public-query implementation endpoint.
