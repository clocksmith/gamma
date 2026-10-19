# Frozen literal-margin fit experiment on 128

The candidate failed the specified acceptance rule. On ten already exposed fit
requests it returned 2 correct answers, exactly the structural control count;
nearest training graph returned 4. There were no wrong acceptances or
infrastructure failures. Candidate route p95 was 5.134 seconds against the
unchanged two-second budget. This run is retained without tuning or retry.

| Arm | Valid graphs | Accepted correct | Wrong acceptances | Abstentions | p50 seconds | p95 seconds |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Raw | 8 | 2 | 0 | 8 | 2.712 | 5.132 |
| Structural control | 9 | 2 | 0 | 8 | 2.715 | 5.132 |
| Literal candidate | 9 | 2 | 0 | 8 | 2.717 | 5.134 |
| Nearest training graph | 10 | 4 | 0 | 6 | 2.697 | 5.008 |

## Mechanism and authority

This executes the existing-assets deterministic development construction proposed
in [the preceding diagnosis](../typed-fit-semantic-diagnosis-128-v1/literal-construction-proposal.json).
It needs no new training, model download, protected scoring, or autonomous agent
loop approval. The opt-in implementation does not change default lookup or old
comparison routes.

The structural control includes the previously tested interior-empty-slot option.
For a structurally valid graph that fails public examples, the candidate orders
active integer literal bits by absolute captured logit margin and selects the
lowest eight. Boolean slots permit only the unit-magnitude bit. It enumerates
one- and two-bit flips by summed margin with a deterministic coordinate tie-break,
validates each graph, and executes at most four additional public-example checks.
It stops at the first public pass. No expected constant, target graph, source
solution, or independent test selects a repair. Rendering uses the existing typed
codec; there is no autoregressive source generation at query time.

The extra construction allowance is at most 0.25 seconds within two seconds for
the complete warm decision. Structural construction and the first public check
are shared with the control and charged in full; all wrapper and repair overhead
is additionally charged. The nearest-graph arm uses the same 15 original qualified
fit graphs and query similarities, with interface-compatible parameter renaming;
it excludes the neural predictor cost. Cold setup and independent scoring are
reported separately.

The predeclared process envelope was four CPU threads, 8 GiB RAM, 5 GiB disk,
and 300 seconds. Acceptance required at least one additional accepted-correct
answer, no lost correct answers, no wrong acceptance or infrastructure failure,
and p95 at most two seconds. Success would be a fit-development signal only.
Neither composition goal nor a release would be qualified by these ten cases.

## Frozen assets and execution integrity

[Candidate manifest](candidate.json) records the exact proposal, source, driver,
dependencies, original artifact hashes and encoder metadata. Its SHA-256 is
`27f14a14446c67fa512dcfda42bee658b8fc97194b21727d581d94fd477e289a`.
The original checkpoint and corpus remained byte-identical:

- Checkpoint: `25f9ca2ff223f5ae930f9511be21445efaa6dde49a697eccd5c648bdb918617c`.
- Corpus: `566d6b440d7fdd16bac0b86114b5e8dd35ba8bd646b6bd304f8cfbc5e201330e`.
- Historical captures: `943777222f5515a865eb57b24a27f15d17b3f400b2388248f69aa0a70fa849a8`.
- Local encoder model: `0437e45c94563b09e13cb7a64478fc406947a93cb34a7e05870fc8dcd48e23fd`.
- Local tokenizer: `def76fb086971c7867b829c23a26261e38d9d74e02139253b38aeb9df8b4b50a`.

All ten newly captured raw predictions matched their historical codes exactly.
The historical inference tokenization was retained for matching; this does not
waive the separate training preflight that rejects truncated inputs. All head
logits, raw codes, candidate choices and correction traces are preserved locally
in `runs/typed-literal-margin-fit-128-v1`. [Capture seal](capture-seal.json) precedes
repair. All forty arm decisions were [sealed](decisions-seal.json) before loading
independent source tests. Original run artifacts were checked unchanged afterward.
[Integrity hashes](integrity.json) preserve the raw run file identities. Raw
solutions, graph labels, tests and model weights remain ignored and local.

Execution used x@128, CPU-only inference in `.venv_rocm`, four CPU threads and a
user scope capped at 8 GiB and four CPUs. The real Linux sandbox probe passed.
Other host workloads remained active; this is not an exclusive-host measurement.
Recorded total wall time was 80.162 seconds, CPU time 226.924 seconds, peak RSS
5,211,643,904 bytes, and counted experiment disk usage 1,295,947,970 bytes.
[Setup](setup.json), [sandbox probe](sandbox_probe.json), and
[aggregate/per-case results](summary.json) retain the measurements.

## What the failure establishes

Seven structural decisions exhausted the complete decision budget; the two
accepted control answers were retained. The remaining case, lcd:1464, had only
about 25 milliseconds left after its 1.975-second control prefix. It attempted
one valid literal change and the public check timed out. No literal candidate
passed. Total additional literal-wrapper/search time across all requests was
0.048 seconds. All five cases previously diagnosed with literal-only defects
were already over budget and never reached literal search.

Consequently this is a failed integrated candidate with very limited evidence
about the repair mechanism itself. The decrease from the earlier four accepted
control answers to two accompanies timing rejection, while exact raw-code parity
rules out changed raw predictions. Embedding dominates the measured phases;
existing host load is observed, not established as the sole cause. The
[timing diagnosis](timing-diagnosis.json) records each phase. No budget relaxation,
post-score retuning, audit rerun or protected opening followed.

## Software checks

Before execution, the new repair tests, typed comparison tests and required judge
and lane tests passed: 50 tests and 5 subtests. After the final wrapper-overhead
accounting adjustment, all 5 repair tests and 2 subtests passed again. New Python
files compiled. These checks establish software behavior, separately from the
solving results above. The named 400-step training proposal remains unapproved.
