# Measured outcome

This bounded source-macro search produces small gains over its matched literal
control. It does not demonstrate the earlier proposed 15–25-word solutions or
an optimal 64/128/256-entry language. The complete tables and exact denominators
are in [RESULTS.md](RESULTS.md).

On the 100 exposed development-validation problems per language, complete packet
costs (including every operand, spelling bit, count, header and padding) are:

| Language | Width | Fragment mean | Mixed mean | Mixed p50 | Mixed p95 |
|---|---:|---:|---:|---:|---:|
| JavaScript | 6 | 247.96 | 249.07 | 189.33 | 537.33 |
| JavaScript | 7 | 199.94 | 196.40 | 153.14 | 396.57 |
| JavaScript | 8 | 166.23 | 162.53 | 126.00 | 323.00 |
| Python | 6 | 552.95 | 552.95 | 444.00 | 1152.00 |
| Python | 7 | 438.94 | 438.72 | 372.00 | 876.57 |
| Python | 8 | 346.42 | 345.93 | 283.00 | 718.00 |

Units are total packet bits divided by width, not just opcode selections.
All 100 validation sources per language reconstruct exactly. All require some
spelling; 100% representation coverage therefore does not establish that the
learned macro vocabulary alone covers those problems. A fit improvement can
regress on validation, as JavaScript at width 6 does.

At width 8 the mixed JavaScript codec averages 66.13 opcode selections, but
spelling alone adds 663.30 bits per source. Raw Python averages 75.69 opcode
selections and 2,052.36 spelling bits. Counting just opcodes would conceal the
dominant cost. The experiment does not establish that every macro design has
this limitation: it screens 24 candidates per width and uses exact segmentation
over admitted AST positions, with heuristic dictionary selection.

The compact-Python static diagnostic reduces the mixed width-8 mean to 158.93
packet word-equivalents (p50 124.50, p95 323.00). It retains 298 transformed fit
sources plus two original fallbacks. All 100 validation sources transform, so
the full and transformed-only validation subsets coincide. These successor
programs have zero fresh native qualifications. This is evidence about a source
rewrite plus refitted dictionaries, not an isolated variable-renaming effect.

The final class-unit exclusion removes one unused JavaScript macro candidate
(1,498 to 1,497); all selected tables, packet measurements and summaries match
the retained second attempt. No validation score selected a dictionary or
triggered additional search. Earlier attempts and their implementations remain
private and hash-linked from the final report.

The implemented artifact is a lossless source-macro codec and comparison
harness. A typed semantic compiler, description-to-program synthesis, human BITS
interaction and fresh native qualification are outside this experiment's proof.
See [development checks](CHECKS.md) and [packet verification](verification.json).
