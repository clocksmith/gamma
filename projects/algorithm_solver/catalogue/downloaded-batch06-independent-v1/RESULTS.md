# Batch six: measured result

The campaign exercised all 120 original JavaScript/Python programs with 29,459
independent cases per language, including all 720 sliding-puzzle permutations and
all 19,683 Tic-Tac-Toe boards. Original execution comprised 60,796 calls in 1,912
isolated batches. All 118 originals outside problem 792 passed typed value and
effect checks.

Both original 792 programs failed the single maximum-size negative subsequence
fixture: 50,000 `a` characters and 5,000 copies of a 50-character `b` word,
expected 0. Each process exited 137/SIGKILL after about 3.01 seconds under the
frozen three-second CPU budget; wall-time and output-limit flags were false.
Those source files and raw failures remain unchanged.

The separate [Python](repairs/792.py) and [JavaScript](repairs/792.js) variants
advance only words waiting for each input letter and preserve duplicate counts.
Both passed the original 63 cases plus two new positive/duplicate controls under
the same limits: 136 calls across 10 isolated batches. Raw observations for both
campaigns were independently replayed on Jupiter and Mars. No candidate ran on
Mars, and no public services were paused.

Problem 760 remains blocked in both languages: its official premium definition
is unavailable. Its provisional mapping-property checks passed, but that does
not establish the normative contract. The other 59 IDs now have two source
variants passing this scoped campaign: 58 unchanged original pairs plus the
repaired 792 pair. The [receipt](evidence/qualification-receipt.json) binds exact
sources, interfaces, observer, runtime, contracts and raw archives. Public
statement text stays in ignored run inputs; only hashes and URLs are in freezes.

The first preparation attempt stopped before candidate execution because a set
changed generator order between processes. Its snapshot, freeze and failure are
preserved. A deterministic sort and cross-hash-seed check preceded the new freeze.
Seven host-reference checks and 37 existing Linux judge preflight checks passed.

These are finite functional `solve` results, not official wrapper execution,
formal proof, official judge acceptance, held-out evidence, retrieval qualification
or catalogue admission. Official metadata names problem 777's second argument
`result`; the local positional adapter names it `end`, without reordering.
Root review and promotion remain separate. Original imports and protected Gamma
payloads remain unchanged; composition stayed paused.

Raw call-count clarification: the frozen baseline `executed_calls` and replay
`calls_replayed` fields count **60,796 attempted call slots**. The raw streams
contain **60,794 complete observation rows** across **1,910 successful interpreter
streams** out of 1,912 sandbox batches. Each original 792 interpreter was killed
before its one maximum-negative fixture emitted an observation. The repaired
variants emitted all **136 observations** from 136 attempted calls across ten
successful streams. Frozen reports and raw files remain unchanged; independently
counted metrics are retained in `evidence/results-v2-call-metrics.json` and
`evidence/repair792-results-call-metrics.json`.
