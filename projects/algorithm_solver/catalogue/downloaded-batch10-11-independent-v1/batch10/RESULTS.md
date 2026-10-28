# Batch ten results

**15/16 pairs (30/32 slots) scoped-qualified.** All 32 original solve functions
pass 3,705 independent cases per language: 7,658 attempted calls, 7,658 complete
observations and 278 complete interpreter streams. No candidate source changed.
1427 String Shifts passes provisional cases but remains blocked because its
primary public definition is unavailable. No active catalogue promotion occurred.

The first run uncovered an owned reader bug: JavaScript's valid JSON string
contained U+0085, which Python `str.splitlines()` incorrectly treated as a record
boundary. The raw stream had three LF records (two observations plus done), while
that parser created nine fragments. Its 31/32 first report is not a candidate
failure claim. The first source/archive/freeze/raw/report remain retained. A
regression-tested LF-only parser, the same candidate bytes/cases/runtime/limits,
and a new freeze yield 32/32 behavioral passes. Both attempts replay exactly on
Jupiter and Mars. No shared adapter was modified.

Seven host reference checks and 37 existing Linux judge preflight checks pass.
Clock-angle outputs accept legitimate finite int/float numeric values with 1e-5
absolute tolerance; booleans/nonfinite fail. Effects and fresh mutable outputs
are checked, and static source review found no caller writes. Official wrappers
are syntax-reviewed only. This is exposed-source finite evidence, not held-out
admission or a universal runtime/correctness proof.

Final freeze `bc8707da080ba9dae5cfc4a20a62aab671589a3dbe6fae2a76514bd537d4a950`.
Exact per-language reports, interfaces and metrics are in `evidence/`. Full raw
and source archives remain under the matching ignored `runs/` directory on
Mars and Jupiter; `evidence/qualification-receipt.json` binds their paths/hashes.
Use `verify.py --statements <snapshots> --freeze freeze-v2.json --output
<results-v2>` to replay the final raw without candidate execution. The first
attempt requires its exact archived `source.tar` helpers and original freeze.
Candidate execution used only Jupiter's existing isolated judge, one interpreter
at a time, 1GiB address space, CPU3s/wall8s, expected values host-only.
