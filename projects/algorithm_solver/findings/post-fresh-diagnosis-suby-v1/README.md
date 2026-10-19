# Finite diagnosis after the consumed fresh recognition test

The frozen [fresh result](../recognition-fresh-suby-v1/README.md) remains **16/36
correct, two wrong acceptances, 18 abstentions**. Commit `36404d2a1`, all 93 fresh
artifact contents/mtimes, 208 original controls and completed nearest-baseline
artifact hashes are preserved. This diagnostic is developer-exposed evidence,
not another fresh test. No fresh case was replayed under the patch.

## Exact failure paths

**Stock ambiguity:** capacity to hold one share does not specify how many trades
are permitted. The request omitted trade cardinality, so one-trade and repeated
trading readings remain possible. It explicitly prohibited fees and cooldown.
The saved parser trace retained no facts: it recognized `no fees` but suppressed
it as an alternative clause because of `or`; its separate `no cooldown` rule did
not recognize shared negation over the coordinated terms. Losing the fee fact
alone would not exclude this source: the selected source also has no fee. Losing
the explicit cooldown prohibition is the material contradiction-filter defect.
The exact statement-bound source profile correctly declares unlimited trading,
no fee and a one-day cooldown. No contradictory source fact was reported.

The selected cooldown score was 0.645609; the repeated-trade runner-up was
0.611358, a 0.034250 gap exceeding the unchanged 0.02 sibling margin. The score
floor also passed. One initially supplied public example agreed, so public
checking could not resolve the omitted trade limit. The margin mechanism is
operating as coded; it is not proof of semantic completeness. Tightening its
number after seeing this gap would not fix missing semantic authority.

**Rank ambiguity:** duplicate occurrences versus distinct values was never
specified. The narrow grammar also does not recognize the exact rank paraphrase,
but adding that paraphrase cannot create an absent duplicate policy. The selected
source profile explicitly counts occurrences. The ordinary kth source scored
0.687608 and passed its supplied public example. The identity guard finds no
compatible same-slug-family sibling, so no sibling uncertainty blocks it. A
material alternative reading need not have a compatible indexed implementation.
This is a missing semantic-completeness gate, not a parser rule that can safely
infer a default, a source-qualification failure or an infrastructure error.

## Implemented bounded defect fixes

[Patch identity and check receipt](patch.json) names the opt-in parser change
`recognition-negative-coordination-dev-v1`: **software-tested, unselected**.
Supported absence concepts (`fee`, `transaction fee`, `cooldown`, `waiting day`)
now retain shared negation under `no A or B` / `no A nor B`, including reversed
order and longer recognized lists. Evidence retains the complete assertion span.
Any additional alternative outside that recognized span, conflicting assertions,
quotation, double negation or hypothetical wording keeps the conservative behavior.
Unprofiled/stale sources remain visible; scores/order, numeric gates, exact path,
missing-example path, source approval and single public-check behavior are unchanged.
The patch never supplies a missing trade count or duplicate policy. Generic
synthetic development tests check both source-contract exclusions and uncertainty;
these are software regression checks, not unseen recognition success.

The proposed training runner now tokenizes every complete fit-memory and query
representation before allocating the encoder and refuses any input exceeding its
actual cap. It records counts only if every input fits, with no truncation.
[Actual preflight](training-preflight.json) rejects two oversized fit descriptions,
zero oversized requests, without a model load, embeddings or training. This fixes
a silent input-loss boundary; it does not make the training proposal runnable.

Focused verification: **26 tests and 44 subtests pass**, four changed Python files
compile and both changed modules import. No application/model campaign was run
for these checks. Existing frozen route/candidate identities remain historical;
source edits intentionally differ from their hashes, so an old sealed resume
requires archival source bytes rather than relabeling the new code as that route.
All old findings and raw receipts remain unchanged.

## Smallest prospective semantic correction

The next development design should add one final missing-requirement gate before
returning a non-exact stored answer. Bound each source's required answer-changing
facets to its statement contract; require explicit, unique query authority for
those facets. Missing/unknown facts must abstain, including when no compatible
sibling exists or its similarity is far lower. Source facts and public-example
agreement must not fill query omissions. Unknown source contracts must not be
removed so that another source silently wins. Exact statement/interface identity
and all existing approval/execution gates stay separate.

Trade cardinality and duplicate semantics are concrete development targets, not
ID-specific branches. The current curated profiles are not a completeness proof;
required-facet declarations and conservative parsing need their own development
review. This semantic gate is proposed here, not silently implemented or claimed
qualified. After a general development implementation and useful/harmful coverage
comparison, freeze a new candidate and author/review a separately unopened set.
Keep the two consumed failures in their original denominator. The historical
full-catalog/absence gate and mandatory ambiguous-input abstention remain unchanged.

## Latency: counts, batching and redundant work

The retained request counts range from 154 to 719 tokens. All 18 unique request
texts include the full statement and signature, stay below 1,024 tokens and are
untruncated. The nearest baseline calls the encoder once per unique request with
batch size one; alternatives are deduplicated by request identity. Matched-route
code captures one query vector and shares it among raw/corrected/nearest routes.
There is no repeated query encoding across those routes to remove.

All 15 fit-graph descriptions are distinct. Setup embeds each once at batch size
one, costing 68.433 seconds in the baseline. Larger setup batches might change
throughput but cannot remove online query cost; a batched offline per-item average
would not be interactive decision latency. [Memory token audit](fit-memory-token-audit.json)
finds **296-1,660 tokens, two descriptions over the original 1,024 cap**. Earlier
'all 18 untruncated' evidence referred to requests, not graph memory. The original
truncated baseline remains intact. Full memory inputs need a separately declared
and qualified encoding policy before training or a new baseline; do not shorten
text, change the cap silently, or reuse the old baseline identity.

The encoder defaults to a returned KV cache that the embedding caller discards.
One fixed pair tested default cache followed by `use_cache=False` on the longest
existing public development request (719 tokens), following one short warmup.
[Contract](cache-contract.json), [probe source](cache-probe.py) and
[summary](cache-summary.json) retain input/source hashes, order and limits.
Vectors were bitwise identical (maximum difference zero), but default forward was
**5.025 s** and cache-disabled **5.311 s**, both already above the unchanged
**2 s complete-route budget**, before ranking, assembly or public execution.
One pair on a shared host does not establish a speed difference or global quality
parity. It supplies no evidence that removing this cache meets the budget, so no
encoder patch, repeated probe, threshold/model change or parameter sweep follows.

Recorded diagnostic counters: 16.579 seconds wall, 47.831 parent CPU seconds,
3,470,245,888 bytes sampled process-tree peak RSS, four CPU cores/threads and
1,306,971,411 bytes monitored disk; within 8 GiB / 5 GiB / 900 seconds. Timing
counts precede final publication. No training, download, new weights or protected
case was used. No inspected implementation fix has demonstrated the existing
complete budget with unchanged quality; this is not a claim of impossibility.

Component: algorithm_solver recognition and composition input preparation.
Intent preserved: retain actual errors, fail closed on lossy input, keep source
qualification distinct from query identity. No authority boundary changed.
Training still needs user approval and a qualified full-text encoding policy;
2b and protected scoring remain unopened. This finite diagnostic is complete.
