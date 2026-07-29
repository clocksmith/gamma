# JANUS Recurrent + Context-Quotient Joint Replay

Status: PREDECLARED INTERACTION TEST / ZERO SCORE CREDIT

## Rationale

The paid CHIRON-shaped recurrent witness and the paid fixed context quotient
were independently positive but individually subscale. Their separately
measured package-adjusted rates arithmetically straddle the nominal design
debt. Those gains cannot be added. One exact joint replay is authorized to
measure their interaction.

This does not reopen either terminal architecture. The recurrent model,
training schedule, quantization, reset length, quotient state count, quotient
hash, causal suffix, confidence bins, and correction alphabet remain frozen.

## Construction

1. Refit the existing JANUS recurrent model deterministically on the same exact
   canonical 10M population and export its complete adjusted P1 stream.
2. Verify the exported JANUS payload and model hashes against the terminal
   receipt.
3. Fit the unchanged 65,536-state paid quotient against the JANUS P1 stream.
4. Encode and decode one complete arithmetic payload under the composed P1.
5. Charge both packages once.

The quotient receives only the JANUS P1, current WRT byte-tree node, and four
previously decoded WRT bytes. Both models remain runtime-causal after their
explicitly transmitted parameters are read.

## Frozen ledger and gates

```text
original parent payload       1,635,137 bytes
JANUS package allowance         183,439 bytes
quotient package             measured canonical blob
combined package ceiling        384 KiB
gross joint gate              3,000 B/M
net joint gate                2,100 B/M
```

The composed quotient must also improve over JANUS alone and beat its shifted
table control. Parent identity, recurrent A/B identity, quotient A/B identity,
complete arithmetic decode, and WRT/raw inverse binding are mandatory.

A valid rejection is terminal for this composition and authorizes no model,
state-count, or blending sweep.

