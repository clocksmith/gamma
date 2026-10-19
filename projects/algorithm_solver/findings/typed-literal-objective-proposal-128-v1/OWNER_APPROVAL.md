# Approval packet: paired literal-objective experiment on 128

**No training has started.** Approve exactly `typed-literal-balanced-pair-128-v1`
if the scope below is acceptable. This is two sequential 400-step arms, 800 total
optimizer steps, using the original recovered development corpus. It does not
approve the older rebuilt-corpus proposal, dependencies, public publication,
protected scoring or service changes. [Machine-readable packet](owner-approval-packet.json)
records full identities and budgets.

## Original and proposed identities

| Role | Identity | Initialization / representation |
|---|---|---|
| Preserved original | `runs/typed-student-v2/model.pt` | Existing seed 17, step 400 checkpoint; CPU float32 encoder, original 1,024-token truncation. Neither new arm resumes it. |
| New control | `typed-literal-balanced-pair-128-v1/control` | Fresh seed 17 initialization; existing `typed_predictor.per_example_loss`; full 2,048-token inputs. |
| New candidate | `typed-literal-balanced-pair-128-v1/balanced` | Exactly the same initial tensors and inputs; only `typed_balanced_loss.per_example_balanced_loss` differs. |

Original checkpoint SHA256:
`25f9ca2ff223f5ae930f9511be21445efaa6dde49a697eccd5c648bdb918617c`.
Original corpus SHA256:
`566d6b440d7fdd16bac0b86114b5e8dd35ba8bd646b6bd304f8cfbc5e201330e`.
Frozen codec identity:
`e91aee58994ae952e2b43406606127689e10688404f2b5c774380dc7a77df7ad`.

Both proposed initial state manifests have SHA256
`eccda374ddfea26a3c57246791e9200c24b9b017c0b448c1f30d365a2e65a7d0`.
This was verified by constructing the 197,612-parameter CPU predictor without any
optimizer steps, encoder allocation, query inference or training. The receipt
hashes each named tensor's bytes, shape and dtype. New trained checkpoint hashes
cannot exist before training; they are explicitly null in the packet.

The exact opt-in candidate objective is implemented and tested. Its source SHA256
is `ff21367f9cf5ac04094c420d2375b3c40aca9420bf36e7031753b81718975a57`.
The control source SHA256 is
`e6732936965200cbc6ca76d41d1d209fcfdc0498d4bc89dd53329c338d8e5f9a`.
Eight focused tests plus two subtests pass, including class-gradient balance,
ignored bits, missing classes and unchanged nonliteral-head gradients. These are
software checks, not learning or solving results. The execution runner must bind
these identities and the full launch contract before its first optimizer step;
there is no authority to launch before owner approval.

## Data separation and encoding change

Use 15 qualified fit graphs from ten fit problems / ten sibling families. All
alternative graphs for the same problem stay together. The nine audit graphs
from eight different problems / eight sibling families are excluded from loss,
retrieval memory and this proposed evaluation. Fit/audit sibling-family overlap
is empty. Neither partition overlaps the protected 60-family reservation.
Shared algorithmic structures and primitive operations are allowed; this is not
a claim that DSU, heap or sorting concepts are held out. The original audit set
has prior comparison exposure and is not a fresh holdout.

All 66 reserved targets remain outside training and scoring. Evaluation uses only
the ten already consumed fit inputs; independent expected outputs never enter
training or public repair. The broader reservation and nearby variants remain
unchanged.

Retain every original digest-plus-JSON fit-memory string and every signature-only
query byte-for-byte. Two fit-memory strings need 1,565 and 1,660 tokens. Even
lossless compact JSON needs 1,125 and 1,189, so the compact shortcut was rejected.
Both new arms instead use a **2,048-token local limit with truncation disabled**;
all 25 fit/query inputs fit. The existing model permits 32,768 positions.
Do not modify the global serving limit or silently remove long examples. Since
both new arms change context together, their difference tests the loss; neither
is a reproduction of the truncated historical run.

Qwen3-Embedding-0.6B weights remain
`0437e45c94563b09e13cb7a64478fc406947a93cb34a7e05870fc8dcd48e23fd`,
with tokenizer
`def76fb086971c7867b829c23a26261e38d9d74e02139253b38aeb9df8b4b50a`.
Read existing local files in place. Encode CPU float32, batch one, then release
encoder memory before predictor optimization. Frozen training vectors may be
shared between arms; measured query evaluation must perform fresh embeddings.

## Objective, configuration and acceptance

The control averages masked BCE over all 129 bits of each supervised literal.
The candidate averages the mean BCE for positive bits and the mean BCE for
negative bits **within each example**. Omit absent classes, ignore `-100`, and use
zero for an all-masked example. Both losses equal log(2) at zero logits. The five
nonliteral heads, minimum loss across qualified alternatives per problem, and
mean across the ten fit problems remain unchanged. Only 74 / 15,093 fit literal
bits are set; balancing is a hypothesis, not a proven remedy.

Both arms use seed 17, width 64, two transformer layers, full fit batch, AdamW
lr 0.001, four fit-memory neighbors, unchanged 43 operation labels, 192 tree slots
and 129 literal bits. One parallel prediction; no autoregressive source generation.
Select only fixed step 400. No sweep, early stopping, audit-driven selection,
result-driven retries or expanded correction bounds.

After sealing both final checkpoints, compare raw, frozen guard repair and
nearest fit graph on identical consumed fit requests. The nearest baseline uses
the exact same 15 fit-memory embeddings, similarities and stable ranking; no
known-answer catalog or expected UID may select a target. Keep four extra public
executions / 0.25 seconds repair within two seconds total. Seal all public decisions
for both arms before independently scoring with original hash-bound source tests.

A useful quality result requires **at least one additional correct raw answer and
one additional correct guarded answer versus the new matched control**, no lost
correct answers, zero wrong acceptances and zero infrastructure failures. Report
whole-literal accuracy and executable correctness, not just bit accuracy. The
unchanged full-route p95 limit of two seconds is a separate requirement; CPU
latency failure must remain visible. No improvement is promised. A pass remains
consumed-fit development evidence, not 2a completion or 2b generalization.

## Total combined resource envelope

- Two sequential arms; **800 total optimizer steps**, at most two configurations.
- **Four CPU threads total**, CPUQuota 400%; **zero GPU training/encoding jobs**.
- **8 GiB aggregate process-tree RSS** and **5 GiB referenced assets plus run disk**.
- **900 seconds per training phase**, at most **1,800 seconds combined training**.
- **2,400 seconds overall**, including preflight, encoding, both arms, fresh-query
  evaluation, public decisions and independent scoring.
- Finish or pause task-owned 1a compute before taking the full four-thread budget.
  Existing external contributors remain untouched. Preserve partial artifacts
  and stop on any limit; no silent restart, extension or adaptive extra run.
- Existing `/home/x/deco/gamma/.venv_rocm/bin/python`, torch 2.12.1+rocm7.2,
  transformers 5.13.1 and NumPy 2.4.4. **No installs, downloads,
  providers, model/catalog/framework changes or security changes.**

## What the GPU result does and does not establish

The existing GPU route measured the frozen original checkpoint on ten consumed
fit inputs: raw 4/10, guard 8/10 at **0.296-second p95**, nearest fit graph 9/10 at
0.166-second p95, zero wrong answers. It used the same fit-memory library and
similarities for the predictor and nearest baseline. The Qwen encoder ran its
existing float16 GPU path on Radeon 8060S; the predictor stayed CPU float32.
Two CPU threads, real GPU matmul probe passed, no HSA override or new dependency.
Six full raw prediction records and one neighbor ordering differ from CPU;
precision equivalence is not claimed. Ten GPU captures repeat exactly across
the preserved failed and completed attempts.

Timing covers fresh query embedding, GPU synchronization/host transfer, retrieval,
prediction, assembly and public verification. Cold setup, fit-memory embedding,
warmup and independent scoring are separately reported. No query cache supplied
these measurements. The CPU comparison reuses complete measured captures from the
resource-rejected combined CPU/GPU process; the successful GPU-only process is
separately frozen. No exclusive-host or simultaneous paired timing is claimed.

Both 27B contributor services were inactive with MainPID0. The 0.8B and 2B
contributors remained running (PIDs 2707 / 2711); current recheck confirms this.
The GPU follow-up took 17.491 seconds; peak process RSS 3.805 GB plus peak GPU reserved
memory 2.510 GB was below its 6 GiB allocation, with 2 GiB reserved for the parallel
catalog work. This finite GPU result does **not** promise the same timing or
precision behavior for new full-context training/evaluation.

## Catalog arithmetic and dependency approval are separate

The historical index has 3,353 entries. Of 66 protected reservation keys, 65 are
present and excluded: **3,353 − 65 = 3,288 eligible**. The absent metadata key is
`lc:largest-local-values-in-a-matrix-ii`; it was not dropped or replaced by this
work. The full 66-target / 60-family reservation remains intact. The 65-entry
arithmetic is not lost solver coverage or 65 failed solutions.

The preserved baseline catalog has 2,481 approvals and 807 eligible exclusions: 685 missing
independent tests, 75 public-path gaps, 26 runtime failures and 21 unusable evidence
cases. Runtime failures split 15 missing Sorted Containers, 10 memory failures and
one missing datetime import. Unusable evidence splits 19 in-place None-only cases
and two checker/input mismatches. These are the requested baseline counts. Today's separately qualified named-output
extension now approves 2,487 entries, leaving 801 exclusions: 685 missing tests,
69 public paths, 26 runtime failures and 21 unusable evidence cases. All 3,288
eligible queries were verified through its explicit wrapper with zero failures,
and the original catalog remains unchanged. The frozen nine-case comparison
returned 0/9 to 6/9 correct, zero wrong answers. See the
[complete result and wrapper](../known-named-output-1a-128-v1/README.md).
This extends exact-known coverage; it does not qualify new-description recognition.

Source imports do not pin a Sorted Containers version. Version 2.4.0 is a proposed
version, not a historical requirement. The separately documented packaging proposal
must specify an upstream artifact hash and judge-visible files because host-venv
installation alone cannot work under `/usr/bin/python3 -I -S`. No dependency
install or download is included in this training approval.

The separate dependency proposal is now exact: `sortedcontainers==2.4.0`,
wheel `sortedcontainers-2.4.0-py2.py3-none-any.whl`, 29,575 bytes, SHA256
`a163dcaede0f1c021485e957a39245190e74249897e2ae4b2aa38595db237ee0`,
Apache-2.0; [official metadata](https://pypi.org/pypi/sortedcontainers/2.4.0/json).
Only after separate approval: fetch the pinned wheel into a local vendor artifact
and pass it as one fixed flat `/task` file. The current sandbox rejects nested
task filenames, and `-I` excludes the script directory from imports. Use a fixed,
manifest-bound zipimport/importlib bootstrap inside the isolated judge; preload
the package and bind `SortedList` for 14 references with implicit usage while
preserving the one explicit import. Keep `-I -S`, read-only mounts, no network and
all existing resource limits. No global pip/venv installation or relaxed sandbox.
Separate judge-integration approval and fresh qualification are required; pin the
wheel/bootstrap and replay the fixed 15 cases before new runtime/catalog approvals.
No download, packaging installation or judge modification happened here.

The [separate dependency proposal](../known-named-output-1a-128-v1/DEPENDENCY_PROPOSAL.md) records all 15 affected identities and the exact upstream wheel URL.
