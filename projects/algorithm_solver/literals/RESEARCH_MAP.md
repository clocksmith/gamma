# BITS research map

Start here to choose one task. The [historical index](INDEX.md) records lineage,
and cohort reports remain the authority for numerical claims.

| Lane | First entry | What it establishes |
| --- | --- | --- |
| Current result | [Fixed-source comparison v1](fixed-source-v1/RESULTS.md) | Frozen run of the [protocol](FIXED_SOURCE_PROTOCOL_V1.md) on 400 paired Python and JavaScript solutions: verified dictionaries, certified bounds, shared against separate. In-sample only. |
| Unrestricted retest | [Fixed-source comparison v2](fixed-source-v2/RESULTS.md) | Frozen run of the [v2 protocol](FIXED_SOURCE_PROTOCOL_V2.md): unrestricted substrings against the matched two-file control, with exact reconstruction and rechecked bounds. In-sample, with no proved optimum. |
| Final measurement, lane closed | [Fixed-source comparison v3](fixed-source-v3/RESULTS.md) | Total encoded size, dictionary and code tables included, for shared and per-language designs against BPE, PathPiece, frequency, GreedTok and LP baselines. The frozen kill bar passed, but the effects are small and predictable from known theory, so BITS closed with a benchmark note. In-sample, no proved optimum. |
| Representation baseline | [Pure 7/8-bit literal comparison](pure-literal-compare-v1/README.md) | Exact reconstruction of 400 known development programs per language, with separate payload, packet and dictionary accounting. Its exposed validation set is not a fresh holdout. |
| Transfer evidence | [Witness length and unseen transfer](witness-length-sweep-v1/RESULTS.md) | Frozen byte-level sweep and replay on four train/test pairs. `jointBest` can use singletons; `greedyDP` is fragment-heavy, not singleton-free. No recorded multi-byte transfer lift in these arms. |
| Held-out selection objectives | [Objective holdout v1](objective-holdout-v1/RESULTS.md) | Five selection rules trained on 400 CodeNet files, frozen, and scored on 200 unseen problems and one untouched project, for tokens and complete archive bytes. `python3 replay.py check` verifies it in seconds; `score` and `train` reproduce it. |
| Capacity evidence | [Capacity reproduction manifest](bits-reproduce-v1/MANIFEST.md) | Rechecks stored witnesses and certificates; it does not repeat search or establish timings. |
| Editor and promotion | [Promotion contract](BITS_PROMOTION.md), [legacy Shared7](demo/README.md) | 256one owns the live editor. Gamma owns experiment data and verification. Legacy profiles are needed for replay even after they leave the picker. |
| Previous research | [Historical index](INDEX.md), [pilot](README.md#historical-pilot-joint-source-and-vocabulary-optimization) | Joint rewriting, counted fragments/macros, staged searches and null results; these are not the active comparator by default. |

## Owner decision, 2026-11-26

From an external review the owner accepted.

- **The contribution is exact certification. Codec superiority is unproven.** The frozen r4 manuscript proves
  110 entries are both enough and necessary for 704 selected three.js files. On A08 the post-hoc defect tree raises
  the lower bound from 69, where the pre-registered method and the baseline both stopped, to 71. A replayed 72-entry
  dictionary leaves the minimum open.
- **Next bet.** On unseen families, test whether checkable trees routinely close gaps that the strongest prior
  bound leaves open, with proof size and verification time frozen as constraints. The pre-registration is being
  written in `capacity-hybrid-certificate-v1/`.
- **Stop.** No tuning on holdouts. A smaller dictionary is not presented as better compression.
- **Codec-claim bar.** Any BITS codec claim needs fresh data, lean-framed zstd and FSST baselines, complete
  accounting of every byte the decoder sees, and a measured p95 lookup latency. The short-record harness's
  golden-byte accounting fixture is the required check (`short-record-decision-v1/STATUS.md`).

## Run, check and replay an experiment

`objective-holdout-v1` is the worked example. Its `replay.py` is the one entry point for checking and reproducing
it. It works in a temporary directory and writes nothing into the folder.

| Command | What it reruns | Clean clone, 16 workers |
| --- | --- | ---: |
| `python3 replay.py check` | Nothing expensive. Frozen checksums; frozen files tracked by Git; manifests against the corpus; the sets complete and split by IBM's clusters and the rank order; the near-duplicate filter shown to have been live; the scorer's files held to the hashes in its log; every verdict of the independent decoder, with padding; the frozen training receipts; `RESULTS.md` and the rule outcomes regenerated; 13 receipts broken on purpose and refused; seven files end to end, one of them needing the escape | 5 s |
| `python3 replay.py score` | The frozen scorer and the independent decoder on all four sets, compared with the committed results | 36 s |
| `python3 replay.py train` | Every dictionary, code table and the training summary from the training files, compared byte for byte; each engine chain read for its end line and length | 59 s |
| `python3 replay.py posthoc` | The two exploratory result files computed after scoring, compared | 9 s |

Measured on 2026-11-26 from a 43 MB sparse clone of the public repository; `replay.py all --strict` passed in 109 s.
Add `--report FILE` for a machine-readable record. A step that could only be checked in part (no Git checkout, another
zstd version) prints `PART`, never `PASS`; `--strict` makes it a failure.

**Before.** Reproducing the scored result took twelve commands on two machines, a 568 MB download and a Python
environment with `pyarrow` (the sequence is in `objective-holdout-v1/SCORER-LOG.md`, 14:04 to 14:10 UTC). There was
no command for retraining: `sha256sum -c SHA256SUMS-FROZEN` fails after a retrain because `train-summary.json`
records run times. **After.** `python3 replay.py all`, 109 s, no network.

Use the levels in order of cost. Run `check` after any edit and before any freeze. Run `score` only when the scorer,
the format or a result file is in question, and `train` only when the training code or the engine is. Hosted CI runs
none of them and should stay that way. Before any run longer than these, write down which result would change the
decision.

### Starting the next experiment in this lane

- **New folder, new version.** Do not edit a frozen folder; supersede it.
- **What carries over:** `bits_oh.py` (archive format, exact parsers, code-table fitting), `score.py` and
  `replay.py`. **What is the experiment:** the hypotheses and decision rules (`PREREGISTRATION.md`), the selection
  rules (`train_arms.py`), the sample rules for test files, and the table of outcomes (`make_results.py`).
- **Order of work:** commit hypotheses and rules; train; write `SHA256SUMS-FROZEN`; run `replay.py check`; commit;
  only then fetch test files. `check` fails if the freeze lists a file Git ignores, which is the one deviation v1
  recorded.
- **Tiny before full:** `check` pushes seven files through the frozen scorer and the independent decoder in five
  seconds. Use it while changing code. Spend a full scoring run only to answer a stated question.
- **Spent test sets stay spent.** A rule designed after looking at `fresh` or `project` needs new test files.

### A check has to be able to fail

Two reviews on 2026-11-26 found 25 places in this lane where a claim of "verified" would have survived a real
failure. None had changed a result. The patterns, and what to do instead:

| Pattern | Where it was | Instead |
| --- | --- | --- |
| A checker promises a check it never performs, or compares a number only with a copy from the same run | `witness-length-sweep-v1/check_unseen_transfer.py` (frozen) | Break a copy of the results on purpose and see the checker fail. `recheck_unseen_transfer.py` does the missing checks; the frozen checker passes on a broken copy and it does not |
| "All N decoded" claimed by counting reports | `make_results.py`, the paper's scripts | Read every verdict the decoder wrote, and its padding |
| Resume from any non-empty output | `codenet-replication-v1/run_replication.py` | Write to a temporary name; move into place after the end marker; resume only from output that carries this run's receipt |
| A time-limit flag or a short result ignored | `train_arms.py` (frozen) | The driver reads the flag and the length; `replay.py check` reads the frozen receipts |
| A skipped check printed as PASS | `replay.py` | A third status, `PART`, and `--strict` |
| A branch that never runs on real data, so "they agree" is 0 = 0 | the escape, in all 80 archives | A made-up input that forces the branch |
| "0 excluded" from a filter that might have parsed nothing | the Python near-duplicate filter | A receipt that shows what the filter found: `audit_near_duplicates.py` |
| An outcome typed as prose in a generator or in the paper | `make_results.py`, the paper | Evaluate each rule once (`out/rule-outcomes.json`); build the sentence from the data or stop when it stops being true |
| A number traced by searching for the bare number | the paper's trace script | Search for the number inside its sentence |

`objective-holdout-v1/test_replay.py` and `codenet-replication-v1/test_chain_guard.py` are the two tests that break
things on purpose. Add a case there when you add a check.

### What is pinned and must not be edited

| File | Pinned by | Known gap, and where it is closed |
| --- | --- | --- |
| `fixed-source-v3/engine.c` | `fixed-source-v3/FREEZE.md`, `objective-holdout-v1/frozen/train-summary.json`, `codenet-replication-v1/results/codenet_results.json`, `short-record-decision-v1/FREEZE-PROGRESS.md` | Writes its chain in place; its BPE pair table (2^20 slots) cannot grow and a full table never returns; the time limit is read only between rounds. Closed in the drivers: `run_replication.py`, `replay.py train` |
| `objective-holdout-v1`: the 34 files of `SHA256SUMS-FROZEN` | that list | See "Known limits of the frozen code" in its README |
| `witness-length-sweep-v1`: runner, checker, preregistration, results | its three checksum lists | The checker skips four checks; `recheck_unseen_transfer.py` (43 s) does them |
| `fixed-source-v3`: the ten files listed in its `FREEZE.md` | that list | `run.sh` does not check its PathPiece seed runs; the 36 seed chains kept from the CodeNet run all end with `stopped=0`. No checker exists for the seed chains of the fixed-source run itself, which are not in this repository |

A new experiment that needs different engine behaviour copies `engine.c` under a new name.

### Friction measured on 2026-11-26 and not yet fixed

- **The harness is rewritten per experiment.** 18 folders here carry their own Huffman or heap coder, three
  their own shortest-path parser, 20 their own checksum files, and there are 59 separate checker scripts. v1 needed
  1092 new lines of format, training and scoring code before it could ask its question. Sharing code is safe
  only for new folders: frozen ones must keep the copies their checksums cover.
- **Ownership is not recorded per folder.** `OWNERSHIP.md` is a hand-off snapshot from 2026-10-20. It does not say
  who owns which experiment now, and it names a private host path.
- **The slowest step was not compute.** Getting IBM's 2 KB identical-problem list meant streaming the 8.3 GB dataset
  archive for 3.5 minutes. That list is now committed in `objective-holdout-v1/metadata/`. The 40 MB Python
  near-duplicate file the selection rule also reads is not in the repository, so replaying the selection itself,
  which `replay.py` does not do, still needs that stream and the 568 MB mirror download.
- **Lint was linting data.** The hosted lint job was red from 2026-11-24 to 2026-11-26 because it checked frozen
  third-party corpus files. They are now excluded in `ruff.toml`; hosted CI is otherwise a smoke test and reruns no
  experiment.

## Archive in place first

Do not rename or remove existing experiment folders on the basis of age. Frozen
checksums, embedded relative paths, Git-source pins and external citations
cross this tree. Treat old evidence as closed for new output, not disposable.
For example, the reproduction manifest requires the `matched80` Git object and
checks several sibling folders, and the length sweep uses `witness-scaling-v1`
cohort identities. For lookup only, use the map above rather than placing another
copy of a report or source tree here.

For new work, keep reusable code separate from each version's immutable inputs,
checksums, small summary, and independent checker. Put scratch outputs and bulk
candidate logs outside Git. To move an old folder later, first inventory all
checksums, verifier inputs and external links, then replay at the original pin
and show that the same entry points work after the move. Keep the old revision
addressable. Never rewrite old manifests or delete raw evidence to shrink a tree.
