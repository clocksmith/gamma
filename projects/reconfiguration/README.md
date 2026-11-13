# Request-specific reconfiguration experiments

This component holds multi-domain evaluations owned by Gamma. The first
[WGSL channel-gain study](../distillation/wgsl/channel_gain/README.md) remains in
its original directory and continues under its own frozen protocol.

The owner's 2026-11-13 direction authorizes preparing and running small parallel
tests where actual device capacity permits. The initial `cross_domain_screen`
maps the selected analytical MLP gain formula to the last two dense layers of
the already-provisioned 27B model on fresh arithmetic, short Python and
structured-text tasks. This changes model and layer indices; it is not a literal
transfer of the 9B configuration. It is a draft exploratory screen until its concrete inputs
and runtime are frozen; preparation is not a cross-domain result.

Use the existing [research roadmap](../distillation/wgsl/RECONFIGURATION-ROADMAP.md)
and [experimental standard](../distillation/wgsl/EXPERIMENT-PROTOCOL.md). Keep the
running shader study's evidence separate. Archived enwiki9 records may inform
methodology; this work does not resume that retired lane.
