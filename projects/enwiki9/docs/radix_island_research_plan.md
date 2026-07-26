# RADIX-ISLAND: Run-Lifted Numeric Event Coding

Status: TERMINAL NEGATIVE / ZERO SCORE CREDIT

## Distinction from terminal RADIX-STC

`radix_stc_context_ordered_numeric_v1` is terminal negative. Its opening-1M
N4 representation regressed by 1,013 native archive bytes because the framed
main and numeric material still traveled through the selected parent.

RADIX-ISLAND is a distinct successor:

- it begins from completed exact WRT emission groups;
- one typed event replaces an eligible digit run;
- numeric values bypass endpoint428;
- the normalized main stream derives island skeletons and stable keys;
- a small integer mixed-radix/delta coder handles the numeric side.

The retired wrapper-level neighborhood remains closed.

## Gate 0: zero-credit regret oracle

The first tool is:

`tools/radix_island_oracle.py`

It binds:

- the selected final pre-truth P1 trace;
- the exact WRT store and dictionary;
- exact WRT-to-raw emission groups;
- maximal eligible ASCII digit runs;
- decoder-derived run and island keys.

Parent digit-event cost is measured in deterministic integer qbits. This is
not an additive archive measurement.

Replacement costs are explicitly charged:

- per-digit or per-run markers;
- long-run length codes;
- truncated-binary mixed-radix values;
- direct/delta mode bits;
- unchanged-field bitmaps;
- adaptive zigzag Rice residuals;
- fixed side framing.

The conservative control charges a two-byte marker for every short run. No
reserved WRT byte is assumed.

## Controls

- `R1_per_digit_direct`: eight marker bits per digit plus direct values.
- `R2_run_direct_optimistic_marker`: four marker bits per run.
- `R2_run_direct_conservative_marker`: sixteen marker bits per run.
- `R3_occurrence_delta_conservative_marker`: length-keyed occurrence control.
- `R3_context_delta_conservative_marker`: exact decoder-derived run keys.
- `R4_island_delta_conservative_marker`: multi-field island keys and deltas.

The oracle passes only if:

- conservative `R4` saves at least 3,000 B/M;
- context-keyed coding beats the occurrence control;
- island composition beats independent context-keyed runs.

## Native authorization

A positive opening oracle authorizes only frozen disjoint oracle replay. Native
work begins only after aggregate distant traces also clear 3,000 B/M.

Native candidates must replay their own changed probability trajectory:

- `R0`: adjacent parent control;
- `R2`: post-WRT run lifting plus direct numeric side coder;
- `R4`: frozen island and delta composition.

Old-trajectory probabilities receive zero score credit.

Canonical 10M promotion requires:

- at least 25,000 gross archive bytes;
- at least 23,000 net bytes after source and framing;
- no more than 64,000 incremental package bytes;
- at least 1.5 percent fewer main predictions;
- at least one percent decode wall reduction;
- exact roundtrip and deterministic second archive.

## Claim boundary

External STC evidence and every oracle result receive zero score credit.
RADIX-ISLAND changes no forecast until a counted native executable produces an
exact archive, source receipt, roundtrip, deterministic replay, memory receipt,
runtime receipt, and disjoint transfer evidence.

## Opening-1M terminal oracle result

Receipt:

`results/radix_island_oracle_opening_1m_v1/decision.json`

The exact WRT/P1 population contains 21,082 eligible digit bytes in 7,448
runs. The parent spends 14,049,529 qbits on those events, or 2.603215 bits per
digit.

The crucial lower bound fails before native integration:

- direct mixed-radix values cost 68,664 bits, or 3.257186 bits per digit;
- direct values alone therefore exceed the parent's digit cost before any NUM
  marker, framing, source, or changed-trajectory penalty;
- optimistic four-bit run markers produce minus 5,463.253 B/M;
- conservative direct run lifting produces minus 16,635.253 B/M;
- conservative context-keyed deltas produce minus 15,748.753 B/M;
- full conservative islands produce minus 15,826.628 B/M.

Context ordering is a small positive primitive: it saves 1,063 side bits versus
the occurrence control. Island composition is negative: it adds 623 bits
versus independently context-keyed runs.

Verdict: `retire_radix_island_insufficient_or_noncompositional_oracle`.

Do not implement native R2/R4, run distant scopes, tune island separators, or
weaken marker accounting. The parent already codes digits below the standalone
mixed-radix entropy paid by this construction. The external BWT-family effect
does not transfer to the selected endpoint's digit-regret economics.
