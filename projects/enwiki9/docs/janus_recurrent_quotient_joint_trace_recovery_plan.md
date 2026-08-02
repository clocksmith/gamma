# JANUS Recurrent Plus Quotient Joint Trace Recovery

Candidate: `janus_recurrent_quotient_joint_trace_recovery_q0_v1`

Purpose: recover the missing exact adjusted P1 trace for the already-terminal
JANUS recurrent plus paid context-quotient 10M composition. This is an
observation artifact for residual attribution. It does not reopen either
component, change the measured archive, or earn forecast credit.

## Frozen inputs

```text
JANUS adjusted P1:
  results/janus_recurrent_quotient_joint_10m_v1/export/janus_candidate.p1

JANUS payload:
  results/janus_recurrent_quotient_joint_10m_v1/export/janus_candidate.payload

paid quotient model:
  results/janus_recurrent_quotient_joint_10m_v1/joint/model.jqdg1

joint payload:
  results/janus_recurrent_quotient_joint_10m_v1/joint/candidate.payload

joint decision:
  results/janus_recurrent_quotient_joint_10m_v1/joint/decision.json

WRT truth:
  results/endpoint428_pair_layer0_online_native_trace_10m_v1/wrt_store.bin
```

The quotient model must deserialize as the exact `JQDG1` schema: 65,536
states, four history bytes, 32 confidence bins, and the eight frozen rational
correction maps. Re-serialization must reproduce the model bytes exactly.

## Certificate

The recovery tool applies the paid table twice to the same frozen JANUS trace.
It requires:

- all input hashes and sizes to match the terminal joint decision;
- the JANUS P1 to reproduce the exact 1,620,395-byte JANUS payload;
- the two adjusted arrays and serialized P1 traces to be byte-identical;
- every adjusted probability to be legal and nonzero;
- both adjusted streams to reproduce the exact 1,617,484-byte joint payload;
- arithmetic decode to reproduce the complete WRT truth;
- the WRT store to remain bound by the existing official inverse receipt.

On success, the tool writes `joint_candidate.p1` and a decision receipt under
`results/janus_recurrent_quotient_joint_trace_recovery_q0_v1/`. The trace is
ignored as a large reproducible artifact; its size and SHA-256 are committed in
the decision receipt.

## Claim boundary

This candidate has expected savings zero and score credit zero. The source
composition remains a terminal fragile screen at 1,765.3 B/M gross and
1,547.152 B/M after both package allowances, below the frozen 3,000/2,100 B/M
gates. A successful recovery authorizes only decoder-visible residual
attribution. A mismatch is an infrastructure failure, not a compression
rejection.
