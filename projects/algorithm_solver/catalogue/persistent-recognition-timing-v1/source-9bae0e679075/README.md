# Persistent description and artifact timing v1

A bounded **goal 1c diagnostic**, not recognition promotion. The already selected
`c65-m12` policy remains fixed (`min_cosine=0.65`, `min_margin=0.12`). Historical
recognition remains **unqualified, 9/40**; faster responses do not improve that
qualification. The old description-applicability guard is neither edited nor
inserted here. No candidate is executed in this mode.

## Fixed workload

- Exactly the first four positions in the existing 52-query development order,
  projected to query ID/text only. Labels, outcomes and other query texts do not
  drive selection. The freeze contains query IDs/positions/text hashes, not text.
- Two ordered passes: **8 description requests**. Each computes a fresh encoder
  vector; no query-vector cache is opened or consulted.
- Each query ranks **all 4,081** competitors. The exact original title cache is
  restored and the exact 54 authorized enriched-document vectors replace their
  positions. Source availability is never a ranking feature or filter.
- After frozen empirical acceptance, retrieve/materialize exact qualified
  JavaScript and Python artifacts using `KnownSpecService`'s live boundary and
  source hash gates. Any missing artifact abstains; never use a runner-up.
- Separately, IDs `leetcode:802`, `leetcode:875`, `leetcode:2406`, two passes:
  **6 exact-ID artifact controls**, with no description recognition claim.
- The 28 confirmation queries stay sealed. No policy search, model training,
  downloads, GPU use, source adaptation or candidate execution.

`prepare.py` is metadata-only. It checks the pinned predecessor contract and
completed-result hash, verifies the already selected policy, validates permitted
54 document IDs before opening combined semantic documents, binds all baseline
and delta receipt/array hashes, and freezes this directory's source hashes.
It does not load NumPy arrays, instantiate the encoder or read candidate sources.

## Persistent path and timings

`run.py` creates one index, one service and one model in one native process. It
explicitly loads/checks the model once **without a warmup query**, then serves the
workload. Reported initialization components include freeze/preflight, index
restoration and imports, service initialization, and model asset hashing/runtime
checks/loading. First-request cost plus initialization is reported separately
from second-pass warm request costs. OS/page cache state is **uncontrolled**;
"cold" means a new process, not cold filesystem pages or an evicted CPU cache.

Every request reports executed stage durations, end-to-end duration and status:

1. fresh query encoding (description mode only);
2. full-population matrix scoring and ranking;
3. unchanged empirical decision plus qualified metadata retrieval;
4. JavaScript live-gated materialization and local hash check;
5. Python live-gated materialization and local hash check;
6. real response serialization, including materialized source bytes in memory.

Exact-ID controls replace stages 1–3 with exact-ID metadata retrieval. Abstentions
serialize a real abstention response and report the stages actually executed.
Errors retain their failing stage and elapsed costs. Resource termination is not
swallowed as an ordinary request error. Success artifacts are hashed and discarded
in memory: reports contain source digests, lengths and receipt digests, **never raw
source**. Artifact serialization measures a local response, not network delivery.
Interpreter startup before the module timer and network delivery are excluded.
Report IO is excluded from request intervals but included in total run time.

No per-request execution is required to measure this artifact mode. Optional
execution is a **separate existing 30-call exact-ID experiment**, not an implicit
extra stage, and is not launched by any file in this directory.

## Budgets, failure handling and launch authority

Existing private CPU venv and exact pinned model/manifests only; 2 CPU threads,
1 interop thread, 8 GiB address space, 300 CPU seconds (305 hard), 240 seconds
wall, and at least 5 GiB effective memory headroom (host and cgroup minimum).
`launch.py` supervises native execution, with 240 seconds then TERM and at most
5 seconds cleanup grace before KILL. The child has the same wall alarm.
Incremental `requests.jsonl` is flushed/fsynced after every request; progress and
terminal report/failure files are written separately. The supervisor supplies a
failure manifest if the child dies before its own failure handler can run.

**Do not launch until main's independent freeze review and native-owner approval.**
The existing freeze says preparation is not permission to execute. Once approved,
the native owner supplies the reviewed freeze digest and a new output directory:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/workspace/shared/deco/gamma \
/usr/bin/python3 projects/algorithm_solver/catalogue/persistent-recognition-timing-v1/launch.py \
  --freeze /workspace/shared/deco/gamma/projects/algorithm_solver/catalogue/persistent-recognition-timing-v1/freeze.json \
  --freeze-sha256 REVIEWED_SHA256 --output NEW_PRIVATE_OUTPUT_DIRECTORY
```

## Verification and interpretation

Host-only synthetic tests cover complete stage costs, eight fresh encoder calls,
threshold/truncation abstentions, materialization tamper, exact-ID separation,
no source exposure, no fallback, fatal resource propagation, metadata tamper and
fixed-order query projection. They do not run the model, load real embedding
arrays, read candidate source, execute algorithms or measure native latency.

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. timeout 60s bash -c '
  ulimit -v 524288
  python -m unittest discover -s projects/algorithm_solver/catalogue/persistent-recognition-timing-v1 -p test_pipeline.py -v
'
```

Inspect every status including errors/abstentions. Four authored queries are not
a representative workload or generalized latency estimate. Exact artifact
qualification, informal recognition, query applicability and candidate execution
remain distinct evidence classes. All original thresholds and protected boundaries
are preserved; no source agreement is treated as specification truth.
