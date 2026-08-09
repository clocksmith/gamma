# NNCP Midpoint plus Cache-32 Joint Replay QM1

Candidate: `nncp_midpoint_cache32_joint_qm1_v1`

QM0 observed a `6,229`-byte incremental gain over the exact full-midpoint
payload, positive incremental thirds, and an `8,127`-byte margin over the
cross-stream control. Its verifier nevertheless retired the candidate because
the expected faithful SHA-256 was transcribed incorrectly.

The QM0 faithful output is byte-identical to both the registered
`faithful_baseline.bin` and the previously independent cache-Q0 faithful
payload:

```text
99c7d04d174f7ba1a30ae5b4af5c5b5d248cf33225713c1de2ed28862b5ec8c6
```

QM1 changes only that expected hash and the candidate/output identities. Every
symbol, trace, probability, mixture weight, cache coordinate, control,
arithmetic operation, threshold, and claim boundary remains frozen from QM0.
The full replay is repeated rather than rewriting the measured QM0 receipt.

The promotion and kill conditions are exactly those in
`nncp_midpoint_cache32_joint_qm0_plan.md`. This remains a zero-credit teacher
trace experiment and cannot make closed LibNC submission-eligible.
