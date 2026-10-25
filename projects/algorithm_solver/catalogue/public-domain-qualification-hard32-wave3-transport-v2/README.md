# Hard32 wave3 canonical integer transport successor

The trusted JS and Python harnesses already serialize exact integers beyond the safe JSON-number range using the same canonical `__gamma_bigint_v1__` tag. The predecessor comparator normalized only JS tags and rejected one correct Python2569 observation. This linked comparator normalizes existing tags in **both** languages at2569 only. It retains exact outer list types, integer values, caller effects and aliases; it rejects bools, floats, malformed/noncanonical markers and cross-problem reinterpretation.

Original55570 freeze, native report and15/16 verdict remain unchanged. Independent prospective replay of all132 original raw calls under this successor yields16/16 and3836 checks, with zero new candidate executions. That replay is supplementary evidence, **not** a new native run or permission to relabel the executed runtime/runner identity. A separately authorized fresh native run under7566 is required before ordinary fixed-lane adoption.

All16 sources,1918 cases/language, runtime/dependency hashes, limits, full validators, effects and packing are unchanged. New controls cover Python/JS large signed integers, malformed tags, bool/float/type drift and cross-ID exclusion. Twelve host test methods pass; independent review and raw replay are separately hash-bound.

Finite scope remains explicit:2573 fixtures reach matrix size100 while the official1000 limit remains in the validator and exceeds unchanged full-matrix transport limits;2663 lexical fixtures have length at most8 while its full official validator allows100000. Neither is a maximum-domain execution claim or universal correctness proof. Protected and unknown payload boundaries are unchanged.

## Completed successor

The later `223cd7a7` freeze moves the test entry guard below every test class;
both direct execution and discovery run all 12 tests. Its fresh native replay
passed all 16 source-language pairs, 3,836 checks and 132 isolated calls under
the reviewed owned-process supervisor. `QUALIFICATION-RESULT-v1.json` binds this
actual run, distinct from the supplementary old-observation replay above.
`SERVICE-INTEGRATION-v1.json` records v24 adoption and all 1,035 gated artifact
readbacks. Historical failures and both earlier freeze identities remain intact.
