# NNCP v3.3 LibNC second-segment embedding contract

Candidate: `nncp_v33_libnc_second_segment_embedding_contract_v1`

The nonzero-memory attention trajectory first differs at `a_embed`, before any
attention arithmetic. Add one observation-only scalar at state zero after the
source slices and reshapes its decoder input. Compare that symbol with the
assumed preceding truth symbol, then index the exact source post-update-one
embedding with the observed value and replay the existing attention trajectory.

Require two byte-identical executions, unchanged parent archive, teacher trace,
post-update states, and all pre-existing internal observations. The observed
symbol must be an exact integer in `[0,255]`. If using it restores `a_embed`,
localize the missing contract to input scheduling. If it equals the assumed
symbol but `a_embed` remains divergent, localize to live-versus-exported
embedding state. Any other result is an infrastructure failure.

Only the localized contract may be changed next. Do not sweep parameters,
widths, memory lengths, tolerances, optimizers, or populations. This diagnostic
has zero score and forecast credit; the forecast stays `109,389,323` bytes and
the verified full-1G score remains unknown.
