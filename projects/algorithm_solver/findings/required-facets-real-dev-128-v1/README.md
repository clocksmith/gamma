# Real-route consumed-development comparison on 128

The required-facet candidate failed the useful-coverage comparison. On the 16
specified retained requests, unchanged control returned seven correct answers;
candidate returned none. Both had zero wrong acceptances and zero infrastructure
errors. The candidate lost all seven control-correct answers and blocked no wrong
acceptances in this cohort. Keep it unselected. No policy, parser, threshold or
contract was tuned after this result.

| Cohort and route | Correct | Wrong accepted | Abstentions | Answer coverage | Full warm route p50 / p95 |
|---|---:|---:|---:|---:|---:|
| Specified 16, control | 7 | 0 | 9 | 43.75% | 0.311 / 0.933 s |
| Specified 16, candidate | 0 | 0 | 16 | 0% | 0.345 / 0.911 s |
| All 24, control | 7 | 0 | 17 | 29.17% | 0.280 / 0.773 s |
| All 24, candidate | 0 | 0 | 24 | 0% | 0.255 / 0.813 s |

Eight controls lack public examples and stop before retrieval in both arms.
Their near-zero times lower the all 24 latency figures. Specified 16 maximum was
1.331s control and 1.193s candidate. Encoder loading/hash verification took
3.593s separately; total measured comparison wall was 19.509s. Existing Reploid
workloads remained active: these are measurements on that host state, not an
exclusive-host performance qualification. Peak sampled aggregate RSS was
5,042,847,744 bytes, with four CPU threads and approximately 1.21 GB of counted
assets. A systemd scope additionally enforced 8 GiB memory and 400% CPU limits.

## Real inputs and preserved authority

[Frozen candidate](candidate.json), [sanitized results](summary.json),
[artifact hashes](integrity.json), and [driver](compare_real.py).
Ignored raw receipts are in `runs/required-facets-real-dev-128-v1/`.

The retained original `recognition-rebuild-dev-suby-v1` control was copied from
suby (2.4 MB); all 207 bound artifact hashes passed. The run used its 66 source
entries, cached source vectors, 24 identical request inputs, original source
approval/exclusions, and unchanged thresholds. Both arms performed actual query
embedding and retrieval independently, in alternating order. Their vector hashes
and candidate lists matched exactly for every query. Full warm route wall includes
embedding, retrieval, gate/approval, adaptation and public execution; it is not
replayed retrieval timing. Setup and post-decision scoring are separate.

The actual approval verifier initially rejected current `typed_scoring.py`, as
expected after the previous composition evaluator fix. An isolated runtime under
`runs/required-facets-approval-runtime-128-v1/projects/algorithm_solver` restores
that one file from commit 36404d2a1 to its exact approved hash, while retaining
the new opt-in gate separately. All 96 original runtime bindings then passed.
The approval manifest was not rewritten or bypassed. Preflight also found
manifest-bound development metadata missing from the isolated copy; those exact
files were copied and verified before any model execution. The first comparison
execution completed successfully; no run was restarted or overwritten.

The already provisioned128 encoder was used in place. Its weights, tokenizer,
config and tokenizer-config hashes were frozen before execution. No downloads,
training, new source approval, fabricated retrieval or approval stubs were used.
All 48 decisions were sealed before source-test scoring. Original control contents
were unchanged, and the control reproduced every historical disposition exactly.

Correctness requires returned code, expected stored identity, original source
approval and passing the retained source test suite. These finite tests are
source-level evidence, not independently authored new-query qualification.
The consumed fresh 36 test was not replayed; protected composition data stayed closed.

## Failure attribution and next decision

Six of the seven lost correct answers had no contract in the intentionally narrow
ten-source stock/rank declaration. The seventh, `stock-repeat`, was rejected
because output evidence was suppressed as uncertain. Across all 24 requests,
candidate reasons were: nine unbound-source, two sibling ambiguity, two uncertain
requirements, one missing requirement, one contradiction, one numeric confidence,
and eight missing-example rejections. None establishes useful new recognition.

This actual comparison supersedes the synthetic behavior check as evidence about
coverage. The gate's structural rejection behavior works, but this declaration
scope and parser are unsuitable as a selected recognition candidate. A next
separately frozen development candidate needs reviewed declaration coverage and
general uncertainty handling before another useful/harmful comparison. Preserve
this failure and do not call this consumed cohort fresh confirmation.

The driver refuses an existing output directory. Reproduction requires a new
named run, the isolated approved runtime on `PYTHONPATH`, the repository
`.venv_rocm/bin/python`, and `ALGSOLVE_EXPERIMENT_ROOT` pointing to the real lane.
Do not change historical manifests to make a newer runtime pass verification.
