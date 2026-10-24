# Independent review: fixed-q support-budget proposal

2026-10-24. Reviewer: codex confirmation_specs. Public metadata and supplied-input
code review only. No private source, multiplier, index, case or dictionary input
was opened; no corpus computation, complexity measurement, binder or runner was
performed. This review leaves item35 and every frozen predecessor unchanged.

## Result before execution

The two proposed fixed multiplier points cannot produce a positive lower bound
for any support budget. This is an analytical limitation of this exact proposal,
proved from accepted public metadata without computing a new support curve.
The support-budget formulation itself is sound; its behavior under newly optimized
multipliers remains untested.

Write the item35 numerator as `L(q) - T_256(q)`, where L is the sum of full-pool
path numerators. Every proposed support-budget penalty `T_k(q)` is nonnegative,
because the multipliers and therefore entry weights are nonnegative. Thus

```
L(q) - T_k(q) <= L(q),
ceil((L(q) - T_k(q))/D) <= ceil(L(q)/D).
```

These are upper limits on what this particular lower-bound calculation can
report. They are not upper bounds on the primal optimum or feasible witnesses.

All values below are exact integers, with `D = 1,000,000`:

| Population | Recorded35 numerator | Recorded35 top256 penalty | L(q35) = sum of300 path numerators | L(q0), exact for every k | Upper limit on the pointwise-max integer certificate at any k |
| --- | ---: | ---: | ---: | ---: | ---: |
| R | -27,266,973,950 | 12,435,442,807 | -14,831,531,143 | -37,980,000,000 | -14,831 |
| naming | -28,259,230,310 | 11,798,958,032 | -16,460,272,278 | -37,943,000,000 | -16,460 |

Both L values are negative for each population. Consequently, even their
pointwise maximum after subtracting any valid `T_k` stays negative throughout
`k = 0,1,2,4,8,16,32,64,128,256`. At q0 every weight is zero, so its exact curve
is the constant -37,980 for R and -37,943 for naming. The q35 support-specific
penalties and exact curves have not been computed; the displayed ceilings do
not claim those values are attained. A private run cannot change this fixed-q
positivity conclusion.

## Evidence and arithmetic checked

- [Item35 public evidence](../length-sensitive-fraction-v1/evidence/results.json),
  SHA-256 `96d7a2b91d8b32a937582561b76df55a6f2036cdd02839e72ea2b73d9b5bf5d6`.
  For each cohort, independently summed
  `arms[].certificate.path_numerators` and checked equality with
  `certificate.numerator + certificate.top_capacity_numerator`.
- [Item33 public evidence](../all-substring-fraction-v1/evidence/results.json),
  SHA-256 `e65cf5213120d4ca0cfa2688856d592536ef98e62b1a6de9ef4b1579f683d2fc`.
  Independently summed `arms[].optimization.certificate.path_numerators`;
  checked its top-capacity penalty is zero and its numerator equals item35's
  `initial_numerator`. Item35 records `initial_q_all_zero = true`.
- Checked the33 certificate `q_sha256` equals35 `parent_q_sha256`, both public
  source-population hashes agree, both capacities are256, both contain300 fit
  programs, all path-key sets match, both denominators equal1,000,000, and both
  recorded arms are complete with `validation_loaded = false`.
- Integer ceilings were recomputed with `-(-numerator // denominator)`, without
  floating-point arithmetic. No new independent replay of the old private
  certificate was performed; this result relies on its accepted public record.

## Mathematical and prototype review

The proposed activation maximum is exact:

```
T_k(q) = max_j A(j) + B(min(256-j,m2)),
0 <= j <= min(k,256,m1).
```

A and B are prefix sums of nonincreasing one-owner and shared-entry weights.
For each exact one-owner count j, taking as many shared entries as available is
valid because weights are nonnegative. Fewer than256 available entries, empty
classes, zero weights and ties require no invented slots. The j=0 alternative is included; taking available zero-weight slots never
changes the maximum. All entries, including singleton characters and unused
paid entries, belong to their actual support class and consume capacity.

Weak duality has the correct direction. A complete path's used occurrence
multipliers sum to at most the total occurrence weights of its paid dictionary;
its penalized path cost is at least L. Hence `D*F >= L - T_k`. Larger k increases
the allowed activation set, so T cannot decrease and the resulting lower bound
cannot increase. Integer ceilings and the pointwise maximum over the same two
fixed q points preserve that monotonicity. At k256 the maximum equals35's
unrestricted top256 penalty numerically, regardless of tie identities.

The suffix interval test in [prototype.py](prototype.py) is correct: no adjacent
owner change inside `[lo,hi)` means exactly one owner. It tests one versus at
least two distinct owners, not the exact number of owners. Repeated or overlapping
occurrences in one source do not turn an entry into a shared entry. Every35 piece
inherits a constant occurrence interval; excluding banned lengths leaves the
remaining words' classification unchanged. Keeping the best256 positive-
multiplicity pieces per class suffices for the best256 scalar entry weights.

No mathematical blocker was found in this supplied-input formulation. Prototype
correctness testing is the author's separate evidence; this review did not run
those tests or claim full-scale independent index verification.

## Scope and next authority

Record this as a fixed-q analytical null and omit the proposed corpus and
complexity runs. It does not establish feasibility at any k, necessary semantic
reuse, a causal role for one-owner fragments, a new impossibility result, M1,
or a bound for other sources/populations. Positive bounds in earlier narrower
pools remain distinct. A support-budget multiplier optimizer would change the
procedure and requires its own hypothesis, design and review; this note neither
authorizes nor rules out that work.

Component intent is preserved: exact evidence contracts, failure preservation,
complete representation scope and closed protected populations. No component
boundary changes or promotion are proposed.
