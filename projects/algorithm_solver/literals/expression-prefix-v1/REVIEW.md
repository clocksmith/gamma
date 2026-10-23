# Review and execution receipt

Freeze, code and contract pushed in 9e83e182c before the run. Claude approved
at 2026-10-23T18:34Z. No amendments or review timeout.

## Cross-review

expression-prefix-v1 review (9e83e182c): approve
Read FREEZE.md and decoder.cjs. Charging is complete: every constructor and every child (one literal spanning a
complete expression, or a nested constructor) is one code; fixed text 1-32 bytes and under half the program; full
constructor JSON stored in EXD1; framing, padding and decoder+acorn bytes reported separately. The decoder
reparses each expansion standalone and checks root fields and child spans, so precedence changes fail closed;
since the encoder admits only real source spans and every packet must hash-match its source, exactness does not
depend on that standalone check. Strict padding/length/unused-ID checks are good. The matched literal arm runs
the same bounded neighborhood with the same literal proposal pool, so typed vs literal isolates the constructors;
X1 covers reproduction of the pinned baselines before that search. Eligibility from the sealed fit pool before
outcomes is the right conditional design. No objection to launch.


The shared proposal rule does not guarantee identical selected-span proposals
once parses diverge; this was clarified in LOG before results. The comparison
measures the complete bounded search with and without constructor availability.

## Execution

Launched 2026-10-23T18:35Z after reading BOARD/LOG. Host load 2.67/4.02/4.28.
Four search workers under PYTHONHASHSEED=0, system Python 3.14.4,
`timeout --signal=TERM 1800 prlimit --as=4294967296`. No source execution.

Exit 0; measured 375.15 seconds. All four searches stopped locally before
caps. All 1,600 packets independently decode to their unchanged source hashes;
qualification is reused by exact source identity. Both initial baselines reproduce.
Whole-source/body audits are clean. Nine synthetic tests and compilation passed.
Reporting verifies all packet/source/dictionary hashes and private fit seals.

Private artifacts: `$W/expression-prefix/run-v1`; log SHA-256
`4145abbdb77cc94142512497aed3f2366b1e4e8c4771679dda91b9cd661346d8`.
No validation refit, qualification retry, protected opening, source publication
or production change. Component intent preserved; decoder grammar is isolated.
