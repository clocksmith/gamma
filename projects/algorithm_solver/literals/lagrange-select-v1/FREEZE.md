# lagrange-select-v1: frozen design (Lagrangian global dictionary selection with exact polish)

## Purpose

This is gamma-team board item 8 (claude), goals 2a/2b. It follows the owner's correction of
2026-10-23: a search that reaches a local optimum does not show that better dictionaries or
search methods cannot help.

[cost-decomposition-v1](../cost-decomposition-v1/README.md) found the fit-only unlimited-substring
oracle at median 21 on dev-val, while the 256-entry dictionary sits at 63.5. Capacity, not missing
repetition, is the binding limit. Every search so far has been greedy or local (refill, swaps,
pairs), and [tail-search-v1](../tail-search-v1/README.md)'s wider proposals did not escape it.
This stage tests a global method of a different kind. It also measures the headroom under a
capacity-aware lower bound, which A's oracles could not give.

Sources and codec are unchanged. Every selection is a canonical literal code plus one Finish per
program, with no new representation.

## Inputs

These come from [cost-decomposition-v1](../cost-decomposition-v1/contract.json)'s allowlist only,
pinned by hash:
- the R shared-style sources, dev-fit 300 and dev-val 100;
- the starting L-R-128 and L-R-256 dictionaries.

The run never calls the historical all-500 loader. The final held-out 100 and the protected 66
stay closed. Dev-val has been measured before and is consumed development data, not fresh
confirmation. Validation sources are opened only after every dictionary of a width is sealed in
`fit-seal.json`.

**Pre-freeze exposure, dev-fit only.** Two smoke runs of 30 and 300 Lagrangian iterations, with
30 polish trials, measured timing and fit-side numbers and never opened validation:
- 0.2–0.35 s per iteration;
- after 300 iterations, best bounds of 26,545 (128 entries) and 18,086 (256), against baseline
  fit totals of 41,684 and 26,108;
- no Lagrangian primal beat the baseline.

## Method ([selection.py](selection.py))

**Pool.** Every substring of 2–64 characters that occurs in at least two dev-fit programs. Complete
sources and `solve` definitions and bodies are excluded, the latter found by
[tail-search-v1/structure.cjs](../tail-search-v1/structure.cjs). On dev-fit that is 223,244
strings with 1,118,337 occurrence edges. The 96 fallback characters are always present, so each
width has B = 2^w − 96 learned slots: 32 at 128 entries and 160 at 256.

**Bound.** Write y_o for the use of pool occurrence o and x_e for the choice of entry e, with
y_o ≤ x_e. Relaxing that constraint with λ_o ≥ 0 gives, for every λ,

    L(λ) = Σ_p shortest path_p(edges cost 1 + λ_o, characters cost 1) − max over |S| ≤ B of Σ_{e∈S} Σ_{o∈e} λ_o.

By weak duality this is a valid lower bound on dev-fit selections for every dictionary made of the
96 characters plus at most B pool entries. It does not cover entries outside the pool: strings
used by only one fit program, strings longer than 64 characters, or excluded bodies.
[test_select.py](test_select.py) checks the bound against brute force on 36 random tiny instances.

**Subgradient steps.** Polyak steps toward the best exact primal, with θ starting at 1 and halved
after 30 iterations without a bound improvement. At most 4,000 iterations or 3,000 s.

**Primal.** Every 10 iterations, three rankings each take their top B pool entries:
- the summed multipliers;
- the current relaxed usage;
- an exponentially averaged usage.

Each dictionary is scored by exact canonical segmentation of all 300 fit sources, and the best
is kept.

## Arms (per width)

| Arm | Start | Then |
| --- | --- | --- |
| control | pinned L-R dictionary | exact local search continuation |
| global | best Lagrangian primal | the same exact local search |
| global_raw | best Lagrangian primal | none (attribution only) |

The exact local search is matched80-v3: greedy refill (shortlist 24), then local search with the
minify-control neighborhood and its chosen-span proposer, 60,000 trials and a 3,600 s safety cap.
The control isolates whether any gain comes from the global start rather than from more
search budget.

## Measurement

Per arm:
- dev-fit selections;
- dev-val selections and complete actions (selections plus Finish), with median, p90, p95,
  worst, and the counts within 32 and 96;
- the single-character fraction;
- dictionary and package bytes;
- polish trials and stop reason;
- per-problem dev-val actions.

Per width:
- the best lower bound and the best primal;
- the gap between the bound and the control's fit total;
- pool size, iterations, stop reason and time.

Every program is encoded and decoded through the canonical codec. The final audit rejects any
entry equal to a complete source or solve body of fit or validation.

**Readiness (frozen).** This is the bar from tail-search-v1 and name-search-v1. Against the
pinned same-width L-R baseline on dev-val, an arm is ready only if all of these hold:
- 100/100 programs decode;
- the whole-solution audit is clean;
- at least 5% fewer actions;
- median and p90 actions both lower;
- at least 60 programs improve and at most 25 worsen;
- the single-character fraction does not increase;
- package bytes are at most 105% of baseline.

Readiness allows only proposing a separately frozen confirmation. It does not touch M1.

## Predictions

- **Λ1:** the control continuation finds no improving move and reproduces the baseline exactly on
  fit and dev-val (14,014 and 8,948 dev-val selections).
- **Λ2:** the final bound is at least 28,000 at 128 and at least 19,000 at 256, but it still sits
  more than 10% below the control's fit total at both widths. The bound is therefore inconclusive
  about how much better a dictionary could be.
- **Λ3:** global_raw is worse than the control on fit at both widths.
- **Λ4:** global after polish is within 3% of the control's fit selections at both widths, in
  either direction.
- **Λ5:** no arm is ready.
- **Λ6:** every program decodes, and the audit is clean.
- **Λ7:** no arm meets the M1 indicators on dev-val.

## Run

Two width processes run in parallel, with PYTHONHASHSEED=0 and one BLAS thread each. Nothing is
executed: sources are fixed and already qualified, so no sandbox runs.

Not claimed: M1; a universal lower bound (the bound covers only pool dictionaries); any
scorer justification; BITS; training. Sources, dictionaries and sequences stay private. The
public evidence holds counts, hashes and aggregates.
