# Deviations

1. 2026-11-27, before any test score existed. The first scorer run stopped at its first step: `explore_scaling.py`
   reads `u{n}.list` in the chain directory to record training bytes, and the lists had not been copied there. The
   lists were regenerated from the frozen `sets/catalogue-train.json` (first n problems by rank), checked byte for
   byte against the lists the chains were trained on, and added to `out/chains/SHA256SUMS`. No frozen file changed;
   no test file was read or scored by that run.
