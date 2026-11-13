# Request-specific reconfiguration experiments

This component holds multi-domain evaluations owned by Gamma. The first
[WGSL channel-gain study](../distillation/wgsl/channel_gain/README.md) remains in
its original directory and continues under its own frozen protocol.

The owner's 2026-11-13 direction authorizes preparing and running small parallel
tests where actual device capacity permits. The initial `cross_domain_screen`
maps the selected analytical MLP gain formula to the last two dense layers of
the already-provisioned 27B model on fresh arithmetic, short Python and
structured-text tasks. This changes model and layer indices; it is not a literal
transfer of the 9B configuration. The [frozen screen](cross_domain_screen/README.md)
completed all 24 requests across six families. Base, gain and shuffled context each
passed 4/6 under the original oracle, with no paired gain advantage. The original
permuted 3/6 includes an interpreter restriction; its unchanged Python function
passes all six cases in ordinary Python, and corrected replay is pending. Preserve
the [original report](cross_domain_screen/RAW-RESULTS-01.md) and
[raw archive](cross_domain_screen/screen-run-01/archive.json).

Use the existing [research roadmap](../distillation/wgsl/RECONFIGURATION-ROADMAP.md)
and [experimental standard](../distillation/wgsl/EXPERIMENT-PROTOCOL.md). Keep the
running shader study's evidence separate. Archived enwiki9 records may inform
methodology; this work does not resume that retired lane.

The original 9B confirmation is still generating (59/176 observed at 13:19:17 UTC
on 2026-11-13); no confirmation quality conclusion exists yet. Three 27B reset
checks were sequential and exact. Separate [Mac synthetic checks](https://github.com/clocksmith/doppler/blob/daede6a0/reports/channel-gain-20261113/synthetic-isolation-receipt.json)
passed tiny two-state gain isolation, reset/discard and failure cleanup; they do not
establish full-model concurrency. Later proposal and self-improvement rungs 6–9
remain unstarted.
