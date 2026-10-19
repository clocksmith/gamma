# Complete library source qualification

All 3,353 entries were inventoried; 65 protected composition aliases were
excluded before execution. All 3,288 eligible exact queries completed. See
[contract](contract.json) and [normalized summary](summary.json).

The original 815 evidence gaps now have explicit dispositions: two protected
exclusions, 685 missing independent tests, 19 unusable imported in-place sets,
82 passing available independent tests, 26 failed checks or resource limits,
and one unusable independent test set. Passing source tests alone is not an
approved answer: the exact public answer path must also succeed.

The source audit deliberately exercised the ungated baseline. Its 10 wrong
acceptances and 530 unqualified acceptances are retained as failures, not erased.
The subsequent [approved serving path](../known-lookup-release-v1/README.md)
excludes unsupported source references and separately checks every eligible
request. That path returned 2,456 independently qualified sources and abstained
on the other 832 eligible entries, without an observed path failure.

Four legacy classification records were normalized by the current reporter,
without modifying raw rows: invalid checker inputs are unusable evidence rather
than wrong candidate output. Raw receipts, frozen runtime and original summary
remain preserved. Independent tests are finite evidence, not proof.

The earlier v2 audit stopped after 1,830/3,288 rows when corrected judging was
qualified in a fresh snapshot; it remains incomplete and is not merged into v3.
Raw v3 source: `/tmp/gamma-qualified-audit-6qa8sO` on host 128, also retained in
the durable checkpoint directory described by the release report.
