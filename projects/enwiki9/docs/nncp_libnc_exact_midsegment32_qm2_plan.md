# Native LibNC exact midpoint-update gate

Candidate: `nncp_libnc_exact_midsegment32_qm2_v1`

## Hypothesis

The exact causal 32/32 update schedule already certified in the ROCm
implementation can be serialized and executed by the source-native LibNC NNCP
codec. The first 32 symbols are coded with the incoming model; a full fixed
64-state training graph is completed with causally irrelevant zero future
inputs; loss is restricted to states 0-31; Adam updates without shifting
persistent memory; states 0-31 are replayed under updated coefficients; states
32-63 are coded and trained; only then is persistent memory shifted.

Both updates use the faithful parent's segment-level learning-rate coordinate.
The archive header carries the schedule flag so the decoder reconstructs the
same trajectory without external instructions.

## Frozen gate

- Population: the exact donor 10,000-symbol raw-prefix population.
- Parent archive: 9,246 bytes, SHA-256
  `097102977cbaa563e460ef87bf88af99ae6409a5fa3902198316f0308300ffc5`.
- Promotion: candidate at most 8,746 bytes, two identical archives, exact
  patched decode and official NNCP inverse, valid serialized schedule header,
  complete source package at most 1,300,000 bytes, decimal-memory pass.
- Kill: any failed identity or less than 500 actual archive bytes. No midpoint,
  learning-rate, optimizer, segment-length, stream-count, or parameter sweep.

This prefix gate has zero score credit. A positive result only authorizes a
source-native maturity gate on a larger identical symbol population.
