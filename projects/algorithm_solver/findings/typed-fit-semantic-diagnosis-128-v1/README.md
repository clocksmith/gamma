# What limits the known-fit composer now

Five of the six unsuccessful fit cases differ from a qualified target only in
literal bits after the existing structural corrections. The remaining case
chooses the wrong recipe. All six already have qualified targets in the original
training corpus; absent known-problem targets are not the immediate limitation.
This does not rule out needing better training examples or optimization.

| Case | Difference from closest qualified fit target | Algorithmic consequence |
|---|---|---|
|1464, maximum product|One recipe: `stable_unique` instead of `heap_sort`|Uses the final two unique input values instead of the two largest occurrences.|
|1046, last stone|One literal bit: decrement 0 instead of 2|Heap-item count fails to decrease after popping two stones.|
|2144, candy discount|Two literal bits: payment threshold 0 instead of 2; cycle 2 instead of 3|Does not implement paying for two and skipping the third.|
|1710, truck units|Two literal bits: sort field 0 instead of 1; ascending instead of descending|Prioritizes box count rather than units per box.|
|1101, earliest acquaintance|Three bits: initial answer 1 instead of -1, endpoint field 0 instead of 2, completion count 0 instead of 1|Uses timestamp as a vertex and the wrong sentinel/completion condition; inherited inference also exceeded the route budget.|
|1489, critical edges|Seven literal bits affecting weight field, indices and component count|Sorts/accumulates endpoints as weights and miscounts edge identities/components.|

For these five literal cases, operations, child/sibling edges, lexical bindings
and types match a qualified target exactly at all supervised fields. The four
successful fit cases match their qualified target fields completely. The
comparison considers every qualified alternative per UID, choosing by nonliteral
error count, then literal-bit count and target hash. This is post-score diagnosis,
not an inference-time oracle or new solving result.

[Reproducible diagnosis](diagnose_fit.py) and [exact counts](diagnosis.json)
bind the original corpus, captures and scored fit replay by hash. No target-derived
patches were applied to returned programs. Raw predictions and scored results
remain intact. No audit rerun or protected access occurred.

## Why investigate literal prediction

Across 15 fit graphs, only 74 of 15,093 supervised literal bits are one: 0.4903%.
An all-zero bit predictor scores 99.5097% bit accuracy while losing crucial values
such as 2, 3, -1 and sort direction. The current loss averages BCE over all 129 bits
per literal, including the mostly-zero high magnitude bits. That imbalance is a
plausible learning limitation, not a causal result: no balanced-loss training
experiment was run. The separate 400-step training proposal remains unapproved,
and its full-text encoding issue is not bypassed.

## Concrete next construction experiment

[Exact experiment specification](literal-construction-proposal.json):
`typed-literal-margin-fit-128-v1`, specified but not executed. It uses the original
checkpoint and corpus, existing local encoder, current repository dependencies,
four CPU threads, 8 GiB memory, 5 GiB disk and a 300-second total cap. No training or
downloads are needed.

Original captures omit literal logits. First recover those logits with the frozen
checkpoint and original representations, requiring every raw prediction to match
the ten historical fit captures exactly. A mismatch stops with preserved evidence.
Historical 1024-token truncation is explicitly retained only for this matched
evaluation; it grants no training authority.

Compare unchanged structurally corrected control against one candidate that, only
after public-example failure, considers one/two flips among the eight lowest-margin
literal bits. Freeze every nonliteral decision. Validate each graph, allow at most
four additional public executions and 0.25s extra repair within the original 2s
total route limit. Order by captured model penalty with deterministic ties; stop
at the first public pass. Independent tests cannot select or guide edits.

Seal decisions before hash-bound source-suite scoring. Acceptance requires at least
one additional accepted-correct fit answer, zero lost correct answers, zero wrong
acceptances/infrastructure failures, and full-route p95 at most 2s. Measure every
repair/execution cost separately. Even a pass establishes only consumed-fit
development progress, not 2a/2b qualification. Preserve the three/seven-bit failures
that two flips cannot address; do not expand budgets after scoring.
