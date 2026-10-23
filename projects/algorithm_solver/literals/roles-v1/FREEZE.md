# roles-v1: frozen design (declare each identifier once, reference it by role)

Owner direction of 2026-10-23, relayed from Mars
(`~/.local/state/deco-goals/gamma-20261023-operand-direction.md`):
- reduce operand-selection cost, not add more components;
- declare each identifier once per program, then reference it by role;
- count every action;
- compare against the shared-style and minified baselines on untouched programs;
- keep correctness fixed through independent execution tests;
- test unfamiliar human users separately;
- predeclare promotion criteria.

Rename-only is a secondary attribution control. The weak structural-v1 256-entry candidate
(T-R-256) is not confirmed or shipped, and BITS is not updated until a candidate beats the live
profiles.

This is goal 2c (structured languages with charged bindings, operands and decoder semantics). It
is a separate representation, not a flat-literal result, and it says nothing about M2 or M3. This
design, the code and the audit are pinned in [contract.json](contract.json) in the same commit,
before any arm runs. A 200-trial smoke run of all 12 arms has already checked the plumbing. It
was measured on 40 dev-fit problems, never on dev-val, and its output was discarded.

## Programs

- **Pools:** [minify-control-v1](../minify-control-v1/FREEZE.md)'s sources, pinned there by hash.
  - **Om:** terser-minified originals, 500/500 qualified. This is the minified baseline's source.
  - **R:** shared-style rewrites. This is the shared-style baseline's source.
- **Partition:** minify-control-v1's split of the scale500 training 400. Every arm fits on
  **dev-fit 300** and is measured unchanged on **dev-val 100**.
- **Untouched** means that no dictionary, slot set or role rule in this stage is fitted on or tuned
  to dev-val. Dev-val has been measured before, as aggregates in minify-control-v1 and
  structural-v1, but it has never been fitted.
- **Final held-out 100:** not opened. Its sources never pass through the role classifier, and no
  measurement includes them. Opening it needs a separately frozen confirmation step and the
  owner's decision.

**Disclosed inspection.** While checking entry forms during design, I printed the first 1,200
bytes of one dev-val minified source (problem 121, a class-method entry), and the manifest entry
string of one final held-out problem (136). That was the entry string only, not its source. No
rule was tuned on either. The role rules below were written from dev-fit sources and the
interface metadata.

## Representation

**Bound names.** A program's bound names are every name it declares:
- variables;
- functions;
- parameters;
- classes;
- catch parameters.

Binding is by name, not by scope. Each occurrence of a bound name is an Identifier node, except:
- member properties;
- property, method and field keys;
- labels;
- meta-properties.

Some names stay unbound and are spelled as text:
- the names the entry interface fixes: the entry function, or the class an entry like
  `new Solution().f(...)` builds;
- names used as shorthand properties, where renaming would change a key;
- every name in a program with `with` or a direct `eval`. Dev-fit has none.

[roles.mjs](roles.mjs) does the classification on the acorn 8.16.0 AST
(`/usr/share/nodejs/acorn`, pinned by its package hash).

**Roles.** These are the owner's five roles plus a residual. They are encoder-side labels, and
decoding never needs them. Each name takes the first role that applies:

| Role | Rule |
| --- | --- |
| input | a parameter of the entry function or method |
| output | returned as a bare identifier from the entry function's own body |
| index | declared in a `for(...;...;...)` initializer |
| queue | receives both an insertion (`push`/`unshift`) and a removal (`pop`/`shift`) call |
| accumulator | any other reassigned name (assignment or update) |
| other | everything else (helpers, constants, elements, callback parameters, tables) |

**Slots.** A slot is a role and an ordinal, with ordinals numbered by first occurrence within the
program. Each slot is one private-use character, and its single-character code is a dictionary
entry inside the same 2^w budget.
- A slot is **active** while its code is in the dictionary. In B it must also have the END code.
- Every occurrence of a name whose slot is active becomes that slot's character. Literal entries
  may therefore contain slots, for example `for(let ⟨index 0⟩=0;⟨index 0⟩<`.
- Names whose slot is inactive stay spelled as text at every use.

**B (bind).** The body is the abstracted text. The code holding a slot's first occurrence is
followed by the name's own literal codes and then END: this is the declaration, made once per
program. Every later use is part of a body code. [decoder.mjs](decoder.mjs) substitutes the
declared names, and the output must equal the source byte for byte (SHA-256).

**N (rename-only control).** The same abstracted body, with no declarations and no END. Each slot
decodes to the fixed identifier `$$` + role letter + ordinal, so the output is a renamed program.
No dev-fit or dev-val source contains `$$`, a `\x01` byte or a non-ASCII character; these were
counted, and nothing else was read. N separates the naming effect from the declaration cost:
- L to N is the naming effect;
- N to B is the declaration cost.

**L.** The canonical flat-literal codec, unchanged. L arms must reproduce minify-control-v1's Fdev
arms exactly.

## Charging: every action counts

Each code is one w-bit selection: literal, slot-bearing, name and END codes alike. Per program:

| Action | B | N | L |
| --- | --- | --- | --- |
| literal: body codes with no slot | yes | yes | all codes |
| reference: body codes containing a slot (the first one binds the slot) | yes | yes | 0 |
| declaration: the codes that spell each name, once | yes | 0 | 0 |
| binding: END closing each declaration | yes | 0 | 0 |
| navigation | 0 | 0 | 0 |
| correction | 0 | 0 | 0 |
| submission (Finish) | 1 | 1 | 1 |

The solver's stream is entered strictly in order, with no cursor movement, and it is final, so
navigation and corrections are zero by construction. The human study measures both for real.

There are no hidden setup savings:
- declarations sit in each program's own stream;
- slot codes and END take dictionary entries and dictionary bytes;
- the decoder's substitution rule is charged as [decoder.mjs](decoder.mjs)'s source bytes in
  B and N.

Package bytes are reported with and without the decoder:
- LTD1 dictionary;
- 41-byte packet headers (magic `LTB1`/`LTN1`, width, dictionary hash, count);
- payload.

The canonical literal decoder is not charged for L, as in every earlier experiment.

**Parse.** Given a dictionary, the body and each name are segmented exactly (minimum codes, the
canonical tie rule). This is exact for the fixed abstraction. It is not a joint optimum over
which slots to activate per program: every active slot a program uses is bound.

## Audit (dev-fit 300 only)

Produced by [measure.py](measure.py) `audit` (sha `94a1f992...`):

| | Om | R |
| --- | ---: | ---: |
| Bound names | 3,177 | 2,364 |
| Bound occurrences | 13,958 | 11,731 |
| Share of source characters inside bound names | 58.8% | 15.6% |
| Characters to spell each name once | 27,989 | 2,436 |
| Slots used by at least 2 problems | 49 | 34 |
| Programs passing every frozen case with every bound name renamed | 300/300 | 300/300 |

Interface exclusions are 300 per pool, one per program; no shorthand or unsafe exclusions.

**Disclosed rerun.** The first audit ran the rename check with 24 parallel sandbox workers. Five
programs were killed with exit 137, with no parity mismatch: 1015, 1079 and 1088 in Om, and 1015
and 1079 in R. Run serially, all five and their originals pass. The pinned audit reran at the
standard 4 qualification workers, and all 600 passed without a retry.

Execution checks now use 4 workers. A sandbox kill with no parity mismatch is rerun once,
serially, and both attempts are kept.

## Arms (12)

Each pool (Om, R) is crossed with each representation (L, B, N) at both widths (128 entries / 7
bits and 256 / 8):
- Fit on dev-fit 300; measure unchanged on dev-val 100.
- Start from the 96-character fallback alphabet. B also starts with END.
- Greedy refill (shortlist 24), then matched80-v3 exact local search with the scale500
  neighborhood, a 60,000-trial cap, a 6 h safety limit and `PYTHONHASHSEED=0`.
- L uses minify-control-v1's proposer: chosen-source spans only.
- B and N propose, first:
  - END if it is absent (B only);
  - the 16 absent slots with the most dev-fit occurrences (support of at least 2 problems).

  Then they propose chosen-source spans mined from text-contiguous runs: the body, and each name
  on its own.
- The search may add or delete slots and END. Pruning never removes them as unused, because a slot
  can be needed only inside longer entries.

## Correctness: independent execution tests

Every decoded dev-val program in every arm is run against every frozen case of its problem:
- B and N: the files [decoder.mjs](decoder.mjs) wrote;
- L: the canonical codec's verified decoded text.

The check is strict parity with the original's baseline outputs, using the existing qualification
sandbox and harness (`style.parity`), deduplicated by program hash. This is separate from the
encoder, the decoder and the hash checks. A failing program fails P1 for its arm and is reported.

## Metrics

Per arm on dev-val 100:
- total actions and their categories;
- selections;
- median, p90, p95 and worst actions;
- programs within 32 and within 96 actions;
- fallback fraction: codes that are one of the 96 alphabet characters, over all codes. For L this
  is M1's single-character selection fraction;
- bytes per selection;
- dictionary, packet and package bytes, with and without the decoder;
- slots kept and entries containing slots;
- trials and stop reason;
- per-problem actions.

Paired per-problem comparisons on actions: B-Om and N-Om against L-Om and L-R; B-R and N-R against
L-R; B against N. Each gives the change, the relative change, the median and p90 against the
baseline's, improved / same / worse counts and the per-problem range.

## Promotion criteria (frozen before any arm runs)

At each width, a B arm is **promoted** only if all four hold against **both** current baselines,
L-R (shared style) and L-Om (minified), at that width:

| | Criterion |
| --- | --- |
| P1 | All 100 dev-val programs decode exactly and pass every frozen case |
| P2 | Total actions at least 5% below the baseline |
| P3 | Median and p90 actions both below the baseline's |
| P4 | At least 60 of 100 programs improve and at most 25 worsen |

If both B arms pass, the one with fewer actions is promoted, with ties broken by package bytes
including the decoder.

- A small median gain that worsens most programs fails P4.
- A total gain carried by a few long programs fails P3 or P4.

A **conditional gain** is the same test against the same-pool L arm only: B-Om against L-Om, and
B-R against L-R. It is reported, and it promotes nothing.

What promotion permits:
- proposing a separately frozen confirmation (the final held-out 100 or a new protected cohort);
- the human study.

Both need the owner's decision. Promotion is not M1. M1 still requires 400 of the frozen 500,
median ≤32, p95 ≤96, fallback ≤10% and no whole-solution entry, with thresholds unchanged. It is
not a BITS candidate: a binding codec is not the canonical codec, and BITS stays unchanged until
a candidate beats the live profiles under [BITS_PROMOTION.md](../BITS_PROMOTION.md).

## Predictions

- **R1:** L arms reproduce the minify-control-v1 Fdev dev-val selections exactly (41,394; 27,098;
  14,014; 8,948).
- **R2:** at both widths B-Om uses at least 15% fewer dev-val actions than L-Om, and more than
  80 of 100 programs improve.
- **R3:** at both widths B-R is not more than 1% below L-R in actions. R already names by role
  with single characters, so a declaration costs more than it saves.
- **R4:** no B arm is promoted at either width.
- **R5:** at both widths declarations cost actions (B-Om above N-Om), and N-Om stays above L-R. R's
  other style rules matter beyond naming.
- **R6:** every decoded dev-val program in every arm decodes exactly and passes every frozen case.
- **R7:** no arm meets the M1 indicator on dev-val (median ≤32, p95 ≤96, fallback ≤10%).

## Human users (separate step, not run here)

Solver compression and human use are separate evidence classes. [HUMAN_STUDY.md](HUMAN_STUDY.md)
plans a study with real, unfamiliar participants. It is not simulated, and nothing in this stage
stands in for it: no playback, scripted users or model-as-user. Running it needs the owner to
recruit participants and to approve the prototype interface.

## Not in this stage

- No learned scorer and no training.
- No bit/hex model and no 400-step run.
- No BITS or 256one change.
- No M2, M3 or assembly claim.
- No ledger, claim or catalog writes.
- Sources, dictionaries, names and sequences stay private. Public evidence holds IDs, counts,
  hashes and aggregates only.
