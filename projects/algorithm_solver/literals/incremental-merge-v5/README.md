# Exact deferred-trace continuation

The v4 ledger reached182 entries on300 development-fit problems:41,810 selections,
median105,p95=295,58.4812% character selections. All51 events independently rechecked.
The128 comparison exhausted its declared local move neighborhood at47,727 selections,
median122,p95=338,77.8616% character selections. Neither is M1; neither proves impossibility.

The v5 engine changes only representation of temporary scoring rows. Randomized
cache tests and693 actual source rows match full tracing. On one real state the
complete4,807-move worklist has exactly the same winner, dictionary and source choices:
60.62 CPU seconds with eager tracing versus17.12 with deferred tracing (3.54x).
No candidate execution is involved in this comparison. New accepted events retain
independent exact segmentation, full literal bytes, packet decode and cost verification.

The256 continuation remains active. Its182-entry starting prefix is preserved by
hash, not replaced by a fresh random vocabulary. Temporary source trace omission
is an optimizer implementation detail, never an uncharged program channel.
