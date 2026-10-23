# Exact fixed-codebook minimum character-fraction certificate

Board21, goal2a diagnostic. Item16 minimized absolute character count C, with N
selections secondary. That need not minimize C/N: using more learned symbols can
lower the fraction without reducing character codes. Determine the exact minimum
aggregate fraction attainable by ANY segmentation for three fixed source/codebook
pairs: item13 control128, control256 and scope_joint256. No dictionary fitting,
source rewriting, candidate promotion or M1 threshold change.

Use the pinned item13 fit300/consumed-validation100 source and qualification
identities, independently for each split. Final held-out100/protected66 remain
closed. These are retrospective diagnostics on consumed development, not fitted
encoder parameters evaluated out of sample. A split-specific coefficient p/q is
chosen using all that split's sources; do not call it a learned transfer policy.

## Exact objective and independently replayed certificate

For complete path choices across a split, C is the sum of selections whose literal
has length one, N the sum of all selections. Within a fixed width, C/N is exactly
the single-character selection-bit fraction. Finish is counted in actions, but is
not a literal payload selection. Framing and padding remain separate storage.
No average of per-program fractions substitutes for this ratio of sums.

Start at canonical minimum-N paths. Use exact integer fractional optimization:
for current reduced p/q, each literal edge costs q*is_character - p. A backward
DAG shortest path minimizes this signed cost, then N, then the ID sequence.
Sum costs across all programs. If negative, update p/q to the resulting C/N;
if zero, the optimum is proved for these fixed sources and dictionary. Every
update strictly decreases the ratio; the finite path set terminates. Cap64
iterations, failing closed if no certificate rather than claiming an optimum.

Independently replay the final coefficient with a forward DAG that enumerates
literal strings directly, sharing neither trie nor backpointers. Require its
summed minimum transformed cost to be exactly zero and its minimum total N at
that cost to match the selected witness. Decode every packet with the independent
canonical decoder to the qualified source hash. The certificate is restricted to
these fixed codebooks and sources; it bounds no other dictionary, rewrite or
representation. Per-program minima can be nonzero; their sum is the certificate.

Compare canonical, min_char (minimize C then N then ID) and min_fraction (minimize
aggregate C/N, then total N then IDs). For three seeds this is3600packets. Every
literal is charged normally, including extra learned-symbol selections used to
lower the denominator ratio. No insertion of new source bytes or empty symbols.
No new source execution; reuse qualification by exact hash. Original dictionaries,
canonical encoding and all previous verdicts remain unchanged.

## Outputs, predictions and resources

Report both splits and every program: selections/actions, median/p90/p95/worst,
<=32/96, absolute character codes/fraction, raw and decoder-source-inclusive
packages, payload/framing/padding, extra selections/actions vs canonical/min_char,
ratio coefficients/iterations, independent certificate sum and minimum-N witness.
Show 10% reachability exactly as 10*p<=q. If false, no segmentation of that fixed
pair reaches the fraction gate, even without an action budget. If true, report the
witness costs and do not infer the other M1 gates. This does not qualify the500.

- F1: canonical paths reproduce all pinned counts.
- F2: all six split certificates replay exactly and all3600packets decode.
- F3: minimum ratio is strictly lower than min_char's ratio on both256validation
  cohorts (R and naming).
- F4: no validation seed reaches10% under ANY segmentation of its fixed source/
  dictionary pair.
- F5: both256validation minimum-ratio witnesses require more than5% additional
  actions versus canonical.

These are predictions, not assumptions or promotion rules. Report failures.
No candidate selection. Five synthetic tests include100 exhaustive paired-text
cases, exact ties, ratio-of-sums, denominator effects, zero/all-character cases,
certificate rejection, missing coverage and iteration cap. No corpus cost probe
preceded this freeze. One process/core8,1GiBaddress space,600-second overall limit;
Python3.14.4, no GPU/solver/model. Freeze/code/contract pushed, then Claude review
or PLAN30-minute timeout before measurement. Reporting remains separate from the
frozen encoder/runner and may be corrected without rerunning or changing choices.

Component intent preserved. Private source/codebook/sequence artifacts stay private;
public evidence contains only costs, hashes and integer certificate metadata.
Owner gates and M1 unchanged; no ledger/catalog/claim writes or production changes.
