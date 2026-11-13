# Request-specific reconfiguration experiments

This component holds multi-domain evaluations owned by Gamma. The first
[WGSL channel-gain study](../distillation/wgsl/channel_gain/README.md) remains in
its original directory and has completed its frozen selection/confirmation protocol.

The owner's 2026-11-13 direction authorizes preparing and running small parallel
tests where actual device capacity permits. The initial `cross_domain_screen`
maps the selected analytical MLP gain formula to the last two dense layers of
the already-provisioned 27B model on fresh arithmetic, short Python and
structured-text tasks. This changes model and layer indices; it is not a literal
transfer of the 9B configuration. The [frozen screen](cross_domain_screen/README.md)
completed all 24 requests across six families. The
[completed corrected replay](cross_domain_screen/REPLAY-RESULTS-01.md) scores
all four conditions at 4/6, with no paired gain advantage. It expands the bounded
interpreter's accepted syntax for inline lambdas and `sorted` keywords while
preserving behavioral cases. The original permuted 3/6 remains recorded in
the [original report](cross_domain_screen/RAW-RESULTS-01.md) and
[raw archive](cross_domain_screen/screen-run-01/archive.json).

Use the existing [research roadmap](../distillation/wgsl/RECONFIGURATION-ROADMAP.md)
and [experimental standard](../distillation/wgsl/EXPERIMENT-PROTOCOL.md). Keep the
shader study's evidence separate. Archived enwiki9 records may inform
methodology; this work does not resume that retired lane.

The original [9B confirmation](../distillation/wgsl/channel_gain/CONFIRMATION-RESULTS-04.md)
completed 176 generations: base and every gain/control condition scored 0/16,
versus 11/16 for the adapter. All non-adapter sources failed the required interface
before compilation. The subsequent [27B exposed shader probe](cross_domain_screen/PROBE-RESULTS-01.md)
completed four responses, scoring base 0/2 and gain 0/2, also at the source-contract
boundary. Its two resets and the screen's three resets were sequential and exact.
No shader or cross-domain gain benefit has been established. Separate [Mac synthetic checks](https://github.com/clocksmith/doppler/blob/daede6a0/reports/channel-gain-20261113/synthetic-isolation-receipt.json)
passed tiny two-state gain isolation, reset/discard and failure cleanup; they do not
establish full-model concurrency. Later proposal and self-improvement rungs 6–9
remain unstarted.
