# palette-names-v1: per-binding naming with a multi-character palette under exact literal cost

## Question

This is gamma-team board item 27 (claude; proposed by codex), goal 2b.
[binding-descent-v1](../binding-descent-v1/README.md) (item 13) renames eligible bindings to single letters a–z.
Multi-character names enter only through swaps of names already in the program. Yet a learned dictionary entry
such as `total` is already paid for. Naming a binding with it can let longer entries such as `total+=a[i];`
cover a whole statement. This stage widens only the target-name set, and keeps everything else matched.

## Inputs

- **Start point:** item 13's selected scope_joint256 dictionary and fit sources, pinned by hash in
  [contract.json](contract.json).
- **Data:** the qualified R allowlist of 300 fit and 100 consumed-validation programs.
- **Exposure:** the seed was selected using dev-val outcomes, so this is adaptive development, not confirmation.
- **Closed sets:** the final held-out 100 and the protected 66 stay closed.
- **Pre-freeze runs:** none on the corpus. Only the four synthetic tests in [test_palette.py](test_palette.py) ran.

## Policy

**Unchanged from item 13.** These come from `binding-descent-v1/rewrite.py`, pinned and imported:
- scope records, capture constraints, `legal()` and `render()`;
- the eval/with/reflection guards.

[palette.py](palette.py)'s `optimize()` is item 13's scope-mode coordinate descent. Its single-binding target set is a
parameter:
- 2 sweeps and at most 6,000 exact scored trials per call;
- pair swaps as before;
- a strict selection improvement is required, with ties broken by source bytes, then text.

**Palette.** At most **40 multi-character names**, in addition to a–z, in this order:
1. identifier-shaped learned entries of the current dictionary, 2–12 characters, longest first, then by text;
2. binding spellings shared by at least two fit programs, most owners first, then by text.

Never used as names:
- JS keywords, and the contextual or strict-mode reserved words (await, yield, let, static, implements, interface,
  package, private, protected, public, enum, async, of, get, set);
- the literals undefined, NaN, Infinity, true, false and null;
- arguments, eval, solve, constructor and prototype;
- common builtins (Math, Number, String, Array, Object, JSON, Map, Set, console, globalThis and similar).

Each binding's forbidden set of unresolved spellings still applies. In the joint arms the dictionary-derived part
of the palette is recomputed each round from the current dictionary, using fit data only. The final palette is
derived from the sealed dictionary and the selected fit sources, written to `palette.json`, and hashed into
`fit-seal.json` **before** validation opens.

## Arms (256 entries, eight-bit)

| Arm | Target names | Dictionary |
| --- | --- | --- |
| seed | none (item 13 replay) | fixed |
| az_fixed | a–z (item 13's policy, continued; the matched control) | fixed |
| palette_fixed | a–z plus the palette | fixed |
| az_joint | a–z | shared local search each round |
| palette_joint | a–z plus the palette | shared local search each round |

The shared local search is matched80-v3 refill, swaps and pairs with the chosen-span proposer:
- 30,000 trials or 600 s per round;
- refill shortlist 24;
- the minify-control neighborhood.

**Fit procedure.** Two rounds. Original R, the seed and every prior variant are retained, and each round reselects the
cheapest source exactly. Every complete source and solve body of every variant is banned from the dictionary.

**Validation.** It opens after the fit seal. For each program it chooses original R or the seed text by exact cost,
then bytes, then text. It then runs two calls of the arm's own policy under the sealed dictionary and the sealed
palette. There is no refit.

**Contrasts.** palette_fixed against az_fixed isolates the palette, and palette_joint against az_joint is the matched
joint contrast.

## Checks and qualification

**Decode and audits.**
- Every final fit and validation source is reparsed by acorn, and a failure fails the run.
- All 2,000 final choices are encoded and decoded through the canonical codec.
- The whole-solution audit covers the final dictionaries.

**Qualification.** A final source equal to the original R hash reuses the original receipt. Changed (id, hash) pairs
reuse a passing receipt from item 13, 14 or 15 by exact hash. Every other changed pair is run on all pinned cases
with strict observation parity: `style.parity`, 4 sandbox workers, no retry or repair. Failures stay in the
denominator. Item 23's retained exit-137 failure on the unchanged seed source of 1079 is historical. This stage
reuses the item 13 and 15 passing receipts for that hash, as item 24 did, and says so.

## Costs and reporting

**Charges:** all literal selections, one Finish, dictionary bytes, eight-bit payload, 41-byte frames and padding.

**Reported:**
- fit and validation totals, median, p90, p95, worst, and the counts within 32 and 96;
- single-character codes and fraction;
- **source bytes**, because longer names can lengthen sources without saving actions;
- multi-character names introduced per call;
- paired better/same/worse counts, and package bytes.

[evidence.py](evidence.py) writes the public aggregates and applies the rules below.

## Predictions

- **P1:** seed reproduces item 13's validation actions (8,504).
- **P2:** az_fixed's validation actions are within ±0.3% of seed's (item 14 found no gain from continuing).
- **P3:** palette_fixed introduces multi-character names and has fewer fit selections than az_fixed.
- **P4:** palette_fixed's validation actions are at least 0.2% below az_fixed's.
- **P5:** palette_joint has fewer validation actions than az_joint.
- **P6:** no palette arm passes the successor rule below.
- **P7:** all choices decode, reparse and qualify, and the audits are clean.

## Decision rules (frozen in evidence.py)

**Readiness.** Against the pinned R baseline (original sources under the pinned L-R-256) the rule is the standing
bar:
- every program qualified and the audit clean;
- at least 5% fewer validation actions;
- median and p90 strictly lower;
- at least 60 programs better and at most 25 worse;
- the fraction no higher;
- package bytes at most 105%.

**Successor.** A palette arm is a successor only if it is ready against R **and** passes the incremental rule
against **both** seed **and** its matched a–z arm:
- strictly fewer actions;
- median, p90 and fraction no worse;
- at most 25 worse;
- package bytes at most 105%.

Successors are ranked by actions, then package bytes, then name. A successor only motivates an owner-approved,
separately frozen confirmation.

## Resources

Five arms, four spawn workers, with each arm pinned to its own cores (16–25) by `sched_setaffinity`. Then four
sandbox workers. PYTHONHASHSEED=0, about 4 GiB per process.

No training, protected opening, publication, BITS change, human study or M1 change.
