# W002 B01–B04: preserved import and diagnostic receipts

100 original JavaScript/semantics pairs were imported byte-for-byte. Actual code
is tracked in `../../runs/js-corpus-wave-002/`; original deliveries and private
execution receipts remain locally preserved. All IDs, packet hashes and delivered
file checksums matched. The owner subsequently directed import-first processing
and stopped qualification work; these earlier results are historical diagnostics.

The existing Linux bubblewrap judge on 128 ran for 92.487 seconds. Docker was not
used. 58/100 submissions passed every available execution group. All 100 used
free-function interfaces rather than the assignment's Solution class, so none was
admitted under that assignment contract. The named-function execution results do
not change that contract or establish full correctness.

The remaining 42 are not 42 demonstrated algorithm bugs. Overlapping flags:
16 missing public-example groups; seven unsupported independent test transports;
22 JavaScript scoring failures; seven Python-control scoring failures. Ordering,
input-domain and transport issues remain unadjudicated. Preserve failed receipts;
do not weaken comparisons or modify submitted code to manufacture passes.

- [Execution summary](execution-summary.json)
- [Review summary](review-summary.json): per-ID counts and diagnostic labels
- [Executed runner](qualify.py): frozen original run, not an automatic import step
- [Private review package identities](review-packages.json)

890 transferred receipt files matched their SHA-256 manifest. Six importer tests
passed before the import-only follow-up. Local judge checks: 10 passed, 27 skipped;
128 judge preflight: 37 passed. No production catalog or protected evaluation changed.
