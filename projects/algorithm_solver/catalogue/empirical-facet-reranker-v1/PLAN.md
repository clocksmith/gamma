# One fixed empirical facet reranker

No claim of sound elimination. Use exact frozen tentative signed facets; deduplicate and drop internally conflicting facets. For each of4081 rivals, sum authoritative facet agreements(+1) and contradictions(-1), with unknown0; divide by number of query facets (minimum1). Negative evidence penalizes a matching excluded authoritative value; a nonmatching/unknown value gains nothing. Adjust cosine by fixed0.05 times this score. All title-only rivals retain raw cosine, no availability filter. Labels never rank; no sweep or fitting.

Hybrid score ranks; actual raw cosine of the selected candidate retains the original cosine threshold. Margin is explicitly adjusted-score margin; raw selected-versus-best-other and global raw-top margins are diagnostics. Thresholds are compared directly, avoiding floating-point score-translation error. Only then is the existing service asked for the same exact identity/language qualified selections as the original decision path. This is a versioned score/margin mechanism change, not unchanged cosine geometry. Same20 policies and exact102/v16 baseline reproduced before comparison.

Only5/52 descriptions previously had tentative evidence, so any gain is bounded by sparse coverage; report zero/negative outcomes. No semantic veto or proof, no title-only elimination, no source/encoder/confirmation, no new thresholds. Existing arrays only,512MiB60CPU60wall. Ten synthetic controls passed, including all20 zero-adjustment policy parity and exact raw threshold boundaries. Freeze before main independent review and execution.

Initial50586 proposal was never executed; its translation-based gate was replaced before review to avoid floating-point boundary drift. Exact source snapshot retained locally.
