# Vocabulary-aware bound-name rewriting

Board item 4, goals 2a/2b. This is offline exact-string source/vocabulary joint
optimization. The canonical decoder is unchanged; every identifier byte and
every syntax byte in the chosen program is emitted by charged literal entries.
There is no decoder-side substitution, free binding, learned scorer or training.

## Inputs and exposure

Use cost-decomposition-v1's pinned R sources and L-R dictionaries, only the
allowlisted dev-fit 300 and dev-val 100. The final held-out 100 and protected 66
remain closed. Previous validation results informed this design; these are
consumed development results, not fresh confirmation.

Tail-search-v1 found little gain from short syntax proposals, while reclaiming
alphabet entries broke three validation encodings. Keep all 96 fallback
characters here. A's identifier single-character attribution motivates aligning
bound names with useful dictionary contexts. It does not predict realized gain.

Pre-freeze exposure: fit-only binding audit, no name search or candidate cost
measurement. On 300 programs, 2,237 eligible names have 11,307 bound occurrences;
five programs are conservatively skipped. Seven synthetic mechanism checks pass.

## Rewrite policy

Acorn parses source; eslint-scope resolves declarations and references. Group
eligible bindings by original spelling, across scopes. Replace all their bound
occurrences consistently using an injective mapping. Shadowing relationships
therefore remain aligned; an unresolved free occurrence of a spelling excludes
that entire spelling. A new target may not be any reserved identifier spelling.
Swapping two eligible spellings is permitted. No substring replacement is used.

Preserve `solve`, `arguments`, function/class names and function/class-valued
variable names. Shorthand property names are excluded; ordinary property keys,
member names and labels are untouched. Skip the entire program for direct eval,
with, or explicit name/toString member access. Unsupported non-ASCII text is
retained unchanged (all pinned R inputs are ASCII). These conservative checks
are not a proof against arbitrary reflection. Independent execution qualification
below is mandatory, and finite tests do not establish universal equivalence.

One rewrite call performs up to two coordinate sweeps. Bindings are ordered by
decreasing occurrence count, then name. For each, try targets `a` through `z`;
an occupied eligible target swaps its current name with the candidate binding.
Score the whole resulting program by exact minimum literal selections under
the current dictionary. Choose a strict selection improvement, tie-breaking by
source bytes then source text. Otherwise retain the source. Stop a sweep early
only when no binding improves. Original and round sources, accepted mappings,
and rejected trial hashes/costs are retained privately, with reproducible code.

## Six arms

At 128/7-bit and 256/8-bit widths, start from the pinned L-R dictionary:

| Arm | Source policy | Dictionary policy |
| --- | --- | --- |
| control | Fixed R | Two bounded search rounds |
| rename | Two rewrite calls | Fixed starting dictionary |
| joint | Rewrite, search, rewrite, search | Alternating exact search |

Fit search retains original and every prior round's candidate as alternatives.
The existing exact joint selector may select any of them; rewrite proposals
start from its current chosen source. Each dictionary round uses the historical
chosen-parse-span proposer, 60,000 trials, 900-second safety cap, shortlist 24,
96 additions, 500 swaps, 16 pair additions, eight pair removals and 150 paired
moves. No kicks or new learned ranker. No alphabet reclamation. Report both
rounds' budgets and stops; time-capped contrasts are budget-limited.

After fit, persist dictionary, final fit sources and a hash seal before reading
validation sources. Validation uses two rewrite calls under that fixed
dictionary, with no dictionary search, test-feedback repair or refit. Controls
leave validation sources unchanged. This is an offline encoder supplied with
the program, not a problem-description solver or autonomous assembly result.

All newly proposed dictionary entries exclude exact full source, solve definition,
and solve body (with/without braces) from every fit variant. Final audit adds
selected validation programs; any whole-solution match fails the arm without
repair. Every packet must independently decode to the selected source hash.

## Qualification and failure policy

Only final selected changed sources are independently executed, after all fit
and validation decisions are sealed. Deduplicate by problem ID and source hash,
across arms. Run every pinned existing case through the unchanged `style.parity`
sandbox/harness and return oracle; require strict original observation parity,
including argument mutations and aliases. Expected outputs stay outside the
sandbox. Original R source hashes reuse their existing qualification.

Qualification is not optimizer feedback: a failed final rewrite is retained,
fails the arm's readiness, and is not repaired or replaced. No automatic retry.
The private receipt retains diagnostics; public evidence reports counts/hashes
only. Test, baseline-observation and population-manifest hashes are pinned in
contract.json before launch. Only the 400 allowlisted cases/baselines are read;
the manifest's other metadata does not authorize opening its sources or cases.

Four search workers; once they finish, four sandbox workers. No overlap between
these phases. Launcher: PYTHONHASHSEED=0, 4 GiB process address-space ceiling,
7,200-second overall cap. Sandbox limits remain 3 CPU seconds, 8 wall seconds,
1 GiB memory per case batch, batch size 16, four workers. A global timeout or
infrastructure failure is an incomplete/failed run, never an omitted denominator.

Seven synthetic checks and Python compilation/import precede launch. Reuse A's
37 passing judge/lane checks because judge/lane code and limits are unchanged.
Publish this freeze, implementation and contract before asking Claude for review;
launch after approval or PLAN's explicitly recorded review timeout.

## Measurement, predictions and readiness

Report both splits and all arms: coverage and qualification, total/median/p90/
p95/worst selections and complete actions, <=32/96 counts, single-character
fraction, category attributions, dictionary/packet/package bytes, header/padding,
rewritten/unchanged counts, rewrite trials/moves, search trials/stops and wall
time. Every successful encoded program adds one Finish; navigation/correction
are zero. Runtime footprint remains unmeasured. Preserve paired ID-level changes.

- N1: searched controls reproduce both pinned validation totals exactly.
- N2: rename reduces validation actions by at least 1% at each width and improves
  at least 50 of 100 programs at each width.
- N3: joint lowers validation actions at least 1% beyond rename at 256 entries.
- N4: all 2,400 selected programs encode/decode and qualify (reuse included),
  and every arm's whole-solution audit is clean.
- N5: no arm meets all M1 cost indicators on validation.

For development readiness, require all 400 selected programs to qualify, all
100 validation programs to decode, and clean whole-solution audit. Against the
pinned same-width L-R baseline, require >=5% fewer validation actions, lower
median and p90 actions, >=60 improved and <=25 worsened programs, nonincreasing
single-character fraction, and package bytes <=105% of baseline. Rank ready arms
by validation actions, then package bytes, then arm name. Report comparisons to
searched control and rename separately. No aggregate improvement excuses a
qualification failure. These thresholds do not alter M1.

Readiness permits only proposing a separately frozen confirmation. Opening any
held-out set, publishing rewrites, BITS deployment, human studies or training
remains at the owner's gate. No claim, catalog or ledger writes. All source,
vocabulary, name mappings, candidate traces and sequences remain private.

Component: algorithm_solver literal research. Intent preserved; source-search
policy changes, canonical representation and production boundaries do not.
