# Review and measurement receipt

Freeze/code/contractc036ba20c pushed before measurement. Claude approved in the
team LOG2026-10-23T19:37Z: lexicographic objectives and inequalities correct,
canonical-sequence equality gives a genuine reproduction check, and fixed-width
code fraction equals payload-bit fraction. It suggested later auditing item10
joint128 and item14 near-misses; those are outside this frozen seed list and were
not added. Any encoder/seed follow-up requires its own freeze and packets.

Ran after approval on core8,one CPU worker,1GiB ceiling,600-second timeout,
PYTHONHASHSEED=0. Measured2.38seconds. Private segmentation-audit/run-v1 and
segmentation-audit-run-v1.log. All6400 independent decodes and all per-program
objective inequalities passed. Source qualification and body legality reused by
hash from item13, with no fresh source execution or case opening.

Four focused tests passed, including150 tiny exhaustive path comparisons under
all four objectives. Compile/import/help checks passed. Report independently
replays all saved private sequences and hashes. T1/T4 true; T2/T3 false.
No promotion, canonical encoder change or production boundary effect.
