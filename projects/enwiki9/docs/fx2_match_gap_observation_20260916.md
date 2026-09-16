# Interrupted-match continuation: bounded information screen

Candidate `fx2_match_gap_observation250k_v1` observes the original trimmed
`fx2_expert_release250k_v3` parent. It does not remove weights or incorporate
any held lexical, residual, attention, or mixture gains.

The valid final-MLP ablation showed a 1875-byte archive regression despite paid
model savings. Keep that exact pruning realization retired. This discovery
selects lenses 5 and 9 deliberately: a causal continuation corridor and a
specialist supplying information the final predictor may miss. The new question
is whether a historical continuation survives one differing byte. It is not
an assertion of novelty in approximate string matching.

Other considered choices: another final-output calibration lacks a new
information source and its closed feature families stay retired; additional
layer pruning would be a forbidden rescue of the preceding realization;
truth-driven deep adaptation still lacks a specified native gradient contract.
The selected observation is bounded to one alignment mechanism and one fixed
calibration, rather than a parameter or architecture sweep.

## Decoder-visible donor and protected parent

The original Match model tracks a historical cursor and a run of matching bits.
For each new byte, record its starting run length. If that run was at least
64 bits and any bit in the byte differs from its historical counterpart, the
following byte has a possible continuation at old cursor plus one. Plus two is
the shifted control. Require both positions to be available decoded history.
Among eligible existing Match models choose the longest starting run, breaking
ties by original model order. Read no donor from an uninitialized or overwritten
slot. The same selected event set serves aligned and shifted observations.

For ring size H, next-write coordinate t mod H and old cursor c, let
r=(t mod H+H-c) mod H. Accept only 3<=r<H and r<=t. The two donor positions
therefore lie at absolute past times t-r+1 and t-r+2, both below t and within
retained history. This proves availability, not predictability.

Activate only after unchanged dictionary pretraining. New fields record state;
they never overwrite the original matching cursor, confidence, counts, history,
probabilities, or learning. The observer must preserve the 33429-byte parent
archive and every actual final Q16 count against the retained original trace.
The native inverse and repeat must reproduce every observation byte. The
synthetic differential additionally compares every original Match field,
map, count table and prediction byte for byte, including ring wrapping.

## One fixed conditional correction

Use eight bit-position rows. At each eligible byte start, its donor is active.
After its first wrong bit, use the parent for the remaining bits of that byte.
Each row estimates donor correctness with KT counts (a+1/2)/(n+1), rounded to
Q16 with ties upward and clamped to 1..65535. Correctness and prefix state update
only after the actual bit is decoded. The source fixes all initial counts to0.

A two-expert posterior mixes that calibrated donor with the unchanged parent.
Each row starts with equal weights totaling 2^32. Predict by integer weighted
average, ties upward, endpoints clamped. Update the parent weight by its exact
integer likelihood fraction, ties upward and clamped to 1..2^32-1. Inactive
steps leave counts and weights alone. State persists across article boundaries;
there are no fitted/transmitted coefficients or tunable rates. D uses the
aligned donor, S the next shifted historical byte with the same state capacity.
A shift is not a complemented donor or a renamed feature label. S can contain
real predictive information; its result limits the mechanistic interpretation.

Both finite replays must decode independently, reproduce their probability and
controller-state sequences, reconstruct the raw WRT input, and repeat exactly.
P must reproduce the original full native archive including its 46-byte framing.
These D/S archives are **conditional**: their decoder consumes the retained
parent-count/donor trace and dictionary. They are not standalone codecs and earn
no native savings or complete-package credit. A future native correction would
need to regenerate these observations, preserve original learning, and pay its
actual source, runtime and packaging costs.

## Exact opportunity ceiling and decisions

For eligible actual-bit parent counts c_i with denominator 65536, the maximum
ideal saving on that fixed event set is sum log2(65536/c_i), granting perfect
predictions. Let Z=product(c_i) and n be event count. Its exact ceiling in bits
is 16n-floor(log2 Z), computed from a balanced integer product and bit length.
This is not a bound on finite coder termination or on a changed parent state.
The floor/ceil proof requires no floating-point approximation.

No coefficient fitting, thresholds, run-length variants or donor-offset search.
The budget is one exposed cold opening [0,250000) population, 151210 WRT bytes,
one fixed D/S calibration, and independent repeated analysis. Positive finite
D gain over both P and S authorizes consideration of exactly one source-priced
native implementation. Otherwise retire this fixed realization. A small ceiling
can reject its opportunity set, not all approximate matching. No larger scope
or full-corpus extrapolation is authorized. Correctness/resource failures remain
incomplete evidence, not compression losses.

Ten native/controller phases: build, clean, rebuild, preprocess, encode, decode,
raw-derived repeat, untraced encode, analysis, analysis repeat. CPU2, memory
9999998976 bytes, swap0, logical scratch16000000000 bytes, aggregate stop3600
seconds. Publish ownership/source then refresh resource admission. Timing is
shared-host diagnostic. Complete package and full1G score remain unknown; the
90M complete-byte objective receives zero credit from this screen.
