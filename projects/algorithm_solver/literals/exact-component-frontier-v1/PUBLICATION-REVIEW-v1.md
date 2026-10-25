# Public-safe checkpoint review

Allow only the explicitly enumerated files in`PUBLIC-CHECKPOINT-v1.json`, plus
that inventory itself. All paths are beneath this new research directory.
No existing admission ledger, source pool, native runtime artifact or live
optimizer state is included or changed. The pending observer diagnostic is **not**
part of this checkpoint; any later subdirectory needs separate review.

## Contents reviewed

-Code: optimizer/index/aggregate-merge implementations, narrow bounded runners,
 and public inert synthetic test fixtures. Source files are treated as data only.
 Metadata paths/hash anchors in runners identify approved local artifacts; they
 contain no credentials, private source text, cases or expected outputs.
-Evidence: aggregate counts/costs, rational statistics, qualified problem IDs,
 source/receipt/dictionary/code hashes, run boundaries and incomplete-work counters.
 Per-entry support contains numeric dictionary IDs and problem IDs, not literal text.
-Prose: method, finite scope, historical failures, measured joint gain, limitations
 and next authorized resume point. No private candidate source snippets appear.

Every JSON artifact was recursively scanned for prohibited payload fields including
`source_utf8`, `source_text`, `vocabulary`, `literals`, raw `dictionary`, `sequence`,
`packets`, `raw_cases`, `stdout`, `stderr` and `expected_output`: **zero hits**.
The review also inspected the code/output paths: real-pool runners persist only
aggregate evidence and hashes; dictionary/packet/source objects remain in memory.
Synthetic text is authored inert test data, not corpus snippets. No binaries,
bytecode, raw packets, dictionaries, private corpus sources or cases are allowlisted.

The genuine joint result is bounded research evidence, not automatic promotion:
255 entries,N35,086,C14,892,median88.5,p95=248,57,502 complete package bytes;
2 qualified fold variants selected, helper retained,123 improved problems and0
worsened. Absolute character use falls, but its fraction rises. Search remains
incomplete with explicit retirement counters. M1 remains unmet. The checkpoint
preserves failed/partial runs and all88 archived frontier states.

Main owns staging/commit/publication. This sub-agent has staged or committed nothing.
