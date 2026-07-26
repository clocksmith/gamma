# SIBYL-MDL: Paid Page-Regime Residual Coding

Status: TERMINAL NEGATIVE / ZERO SCORE CREDIT

## Question

Can a small label transmitted before a page identify how the selected
endpoint428 predictor will be wrong on that page, with enough paid arithmetic
gain to address the 108,000,000-byte design target?

SIBYL does not infer semantic page categories. It partitions pages by residual
loss under decoder-visible probability states. The encoder may inspect the
complete page when selecting a label because the label is transmitted and
fully counted before probabilities depending on it are used.

## V0: fixed calibration oracle

V0 uses the selected source-bound binary's existing `CMIX_P1_TRACE`. The trace
is emitted before `Perceive(bit)` and therefore records the exact final P1
used by the arithmetic coder. No source mutation or component trace is needed.

The fixed oracle family contains sixteen monotone integer P1 maps:

- identity;
- seven confidence scale maps;
- six signed bias maps;
- two combined shrink-and-bias maps.

The oracle chooses one map per complete page using complete-page truth. The
choice is charged as a fixed four-bit label plus one fixed framing record.
Outside exact complete-page WRT intervals, the parent probability is unchanged.

Controls:

- `Z0`: exact parent replay.
- `Z1`: one globally selected calibration.
- `Z16`: paid pagewise selection.
- `ZR`: the same labels rotated across pages.
- `ZP`: causal title/prefix prediction, withheld until the oracle gate passes.

## Evidence contract

The trace manifest must prove:

- trace rows equal coded WRT bits;
- truth bits equal the exact WRT store;
- exact WRT reconstruction equals the raw input;
- final-P1 range replay equals the parent arithmetic payload;
- every charged page interval begins and ends on WRT event boundaries;
- all inputs, outputs, the source-bound binary, page map, and labels are hashed.

The V0 assignment is chosen with deterministic integer qbit costs. All reported
payloads are then replayed through the exact 32-bit CMIX range-counter state
transition and termination rule.

## Gates

The opening 1M run is sign and leverage discovery only.

Canonical 10M authorization requires the opening net rate to project to at
least 45,000 bytes. The frozen canonical trace must then show at least 45,000
bytes of paid oracle headroom before any component trace or native decoder is
built.

A constructive V1 must independently show:

- at least 30,000 gross bytes at canonical 10M;
- at least 23,000 net bytes after labels, codebook, source, and framing;
- at least 2,000 bytes per million on offset-500M;
- exact deterministic replay and roundtrip;
- no more than five percent runtime overhead.

If V0 misses its gate, simple page calibration is retired. Bits-back,
additional curves, component traces, and capacity sweeps are not authorized to
rescue weak headroom.

## Claim boundary

V0 is future-informed oracle evidence and receives zero score credit. It does
not change the selected forecast, establish native gain, prove transfer, prove
runtime eligibility, or prove a full-corpus score.

## Opening 1M terminal result

Artifacts:

- `results/endpoint_final_trace_1m_v1/manifest.json`
- `results/sibyl_page_prompt_opening_1m_v0/decision.json`

The trace certificate passed all identity gates. It contains 4,805,936
pre-truth rows for 600,742 coded WRT bytes, reconstructs the exact raw input,
and reproduces the parent's 173,859-byte arithmetic payload.

Results over 171 complete pages covering 982,919 raw bytes:

- `Z0`: 173,859 payload bytes, exact parent identity.
- `Z1`: zero gross gain and a one-byte charge, net minus one byte.
- `Z16`: six gross arithmetic bytes saved, 102 label/framing bytes charged,
  net minus 96 bytes.
- `ZR`: 1,196 payload bytes worse and 1,298 bytes worse after charges.

Verdict: `opening_sign_negative_retire_simple_page_calibration`.

Simple paid page calibration is retired. Component tracing, additional curve
families, bits-back labels, and a larger unchanged replay are not authorized.
The selected forecast and 1,524,268-byte design debt remain unchanged.
