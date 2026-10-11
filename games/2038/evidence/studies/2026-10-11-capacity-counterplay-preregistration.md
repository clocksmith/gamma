# Capacity Operator counterplay — preregistration, 2026-10-11

Component: Mandate 2038 policy evidence. Intent preserved. No rules candidate.

Freeze this protocol before selection or confirmation. The preceding fresh-seed
study found Capacity Operator ahead of the authored roster, without qualified
dominance. Test whether stronger opponents or an individually useful response
can answer it. This is simulation, not a human playtest or balance qualification.

## Frozen design

- Canonical executable 0.24.3, rules candidate 0.14.0-rc.4-test, engine 0.27.3.
  Empty rules overlay; retain every faction ability, economy and scoring rule.
- Separate homogeneous `weighted` and `greedy` populations. Every participant
  sees the same public-information contract and uses the same legal policy class.
- New root `capacity-counterplay-128-20261011-v1`. Distinct seed namespaces for
  general training, response selection, adaptation, smoke and confirmation;
  no previous study's seeds and no selection from confirmation outcomes.
- General training: each of seven personas receives four candidates (itself
  plus three seeded mutations, magnitude 0.75), each evaluated on 48 four-player
  blocks: six focal institutions, four focal seats, both objective modes.
  Rotating authored opponents exclude the focal persona. Select by own mean
  winner credit, then own mean score, then candidate index. No sequential search.
  This equal search budget controls preparation; it does not prove equal skill.
- Select the highest-ranked non-Capacity generalist as the responder parent.
  Response search: incumbent plus three mutations, identical 48-block budget,
  maximizing the responder's own winner credit against the trained Capacity
  Operator and the trained field. Focal role is Capacity; rotate responder seat
  among other seats. Adaptation gives Capacity the same four-candidate budget
  against the selected responder. Neither search rewards sacrificial denial.
- Freeze selected profiles, their full strategy hashes and search outcomes in
  a separate selection artifact before any confirmation game.
- Six common-seed arms: original Capacity versus authored field (`authored`);
  original Capacity versus trained field (`field`); trained Capacity versus
  trained field (`equal_budget`); replace one trained rival with its targeted
  responder (`counter`); replace Capacity with its selected adaptation
  (`adapted`); trained Capacity strategy at every seat (`mirror`).
  Mirror is a symmetry/decision-strength control, not proof of diverse routes.
- Confirmation: 3/4/5 players, six focal institutions, every focal seat,
  both variable/fixed objectives, respectively 4/16/4 repetitions per backend.
  This gives 144/768/240 paired blocks per backend, each with all six arms.
  Institution rosters are unique cyclic windows anchored at the focal seat;
  rival personas and responder seats rotate deterministically. Every arm of a
  block preserves the seed, institutions, seats, objective mode and backend.
- Per backend: 1,728 search games + 6,912 confirmation games. Both backends:
  **17,280 games**. Stop at these fixed allocations, or retain an execution
  failure. Do not add candidates, seeds or runs after examining results.
- Also run one 480-match-cap canonical unified audit with a separate root,
  initial coverage 1, batch size 24, workers 2, unchanged registered thresholds.
  It remains general coverage and does not substitute for the targeted study.

## Inference and decision

Primary authority is four players; three and five remain separately reported
guards. Six paired winner-credit effects are frozen: field suppression,
general Capacity recovery, responder own gain, Capacity suppression by the
response, adaptive Capacity recovery, and responder retention after adaptation.
Publish all six at all three counts and both backends (36 effects), using
fixed-look bounded Hoeffding intervals with Bonferroni family alpha 0.05.
Paired differences lie in [-1, 1]; tied winners split credit. Do not replace
these bounds with a favorable unadjusted significance test. Institution, seat,
mode, score, action mix, trades, AGI and mirror summaries are descriptive.

An individually useful counter requires the lower bounds of **both** responder
own gain and Capacity suppression to exceed 0.04 at four players in each
backend. Adaptive recovery requires its own lower bound to exceed 0.04.
These practical thresholds reuse `counterRecoveryMin`; they do not alter the
existing balance contract. Failures to clear a bound remain inconclusive, not
proof that counterplay is impossible. Equal search budgets and a common backend
do not establish human-equivalent opponents or globally optimal responses.

Require finite, nonnegative holdings; complete games; unique Org ownership;
valid board positions; bounded trade packets; zero policy fallbacks; and retained
forced-no-op rates. Check rich/batch projection equivalence on smoke inputs.
Bind clean source, input files, runner, protocol, policies and exact fingerprints.
Abort on identity drift. Preserve every run outcome, including failures.

No automatic economy, scoring, faction, default-policy or deployment change.
An uncountered result in this limited policy family cannot alone justify a rule
change. A persistent advantage would require a named causal mechanism and a
separate one-lever experiment, followed by explicit rule selection. Human
negotiation, learning, enjoyment and blind teachability remain untested.

## Reproduction

Run from `games/2038` on the clean committed protocol/runner revision:

```bash
node --test tests/capacity-counterplay.test.mjs
node evidence/studies/2026-10-11-capacity-counterplay.mjs --backend weighted --smoke
node evidence/studies/2026-10-11-capacity-counterplay.mjs --backend greedy --smoke
node evidence/studies/2026-10-11-capacity-counterplay.mjs --backend weighted
node evidence/studies/2026-10-11-capacity-counterplay.mjs --backend greedy
npm run simulate:audit -- --maximum-matches 480 --initial-runs 1 --batch-size 24 --workers 2 --seed capacity-counterplay-128-20261011-v1-unified --pre-registration-id capacity-counterplay-128-20261011-v1 --output /tmp/capacity-counterplay-unified.json
```

Raw JSON is local under `evidence/studies/simulation/`; track a dated results
receipt with hashes, complete outcomes, limitations and the affected-surface audit.
