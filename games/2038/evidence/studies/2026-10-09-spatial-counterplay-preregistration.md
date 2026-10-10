# Spatial choices and counterplay, current rules

Registered before training or confirmation results. Evidence class: bounded
deterministic-policy simulation, not human play or mathematical unsolvability.
No geography or scoring treatment is authorized by this study.

## Frozen question and boundaries

Can the nineteen-district map support opponent-dependent placement, competitive
alternative plans and individually useful counterplay under current rules?
Test the actual game, including local Power, Facility scarcity, Venture consent,
post-Audit objectives and final offline penalties. Do not substitute varied
random placements for evidence of useful choices.

Release: executable 0.22.2, engine 0.25.2, rules rc.16. Mechanics remain those of
0.22.1 / rc.15. The new executable corrects the Venture response packet: it
exposes proposer, both fixed hosts, current power status and reciprocal nominal
income. Previously these public offer terms were absent. Default policies,
prices, starts, scoring and random-number streams are unchanged. Browser choice
context displays the same offer; no publication is authorized.

Source commit, release identity and SHA-256 hashes of this registration, runner,
diagnostic policies and runtime inputs must accompany the receipt. Run from a
clean committed checkout and verify the sealed release. Raw complete-game
outcomes and location traces belong in the local simulation archive; retain a
tracked receipt and hash. Never rewrite historical reports.

## Policy population and isolation

Nine fixed plans: authored, immediate resource benefits, Compute production,
Power coverage, district control, partner geometry, rival-space denial, refusal
of Ventures benefiting a current score leader, and mixed spatial priorities.
Weights are hypotheses fixed in the companion policy module. All read public
observations only; none can read hidden Training order, future Headlines,
opponent selections or the engine object.

Every policy first asks the unchanged ordinary policy for an action bundle.
Spatial plans may then change destination, Agent, host or partner among legal
decisions with that same action/mode/project/source/recruitment count. They
cannot introduce extra actions or resources. The refusal plan additionally
changes legal accept/reject choices on public Venture proposals. It refuses
strictly leading proposers; this is a heuristic, not solved deal valuation.

Half the blocks use ordinary policies, half use the existing named
`infrastructure_plan_v1` for all seats, selected by `(faction + seat + repetition)
parity. The latter is an explicitly shared construction scaffold that exercises
Power and projects. Publish both ecologies separately. Never call its forced
construction goals observed human behavior. All four/five treatment arms within
a block share it. Both homogeneous weighted and greedy backends are retained.

## Train, counter, adapt, confirm

Four players are primary. Training blocks cross all six focal factions, all
four focal seats and both backends: 48 blocks per stage. Each stage has a distinct
seed prefix. Factions occupy successive canonical IDs from the focal faction;
profiles rotate through all seven current profiles. The responder is one rival
seat, rotated by faction and repetition; other rivals remain ordinary. This is
individual counterplay, not a coordinated coalition.

1. **Placement search:** evaluate all nine focal plans against ordinary rivals.
   Select by focal fractional win credit, then mean focal score, then plan ID.
2. **Counter search:** freeze that champion. Evaluate all nine plans at the
   responder seat. Select by responder fractional win credit, then responder
   mean score, then plan ID. Do not select a losing response merely because it
   hurts the champion.
3. **Adaptation:** freeze the responder. Evaluate all nine focal plans against
   it, using the same focal selection criterion.
4. **Confirmation:** freeze all three selected plans before accessing held-out
   results. All six factions × every focal seat × both backends × four repetitions
   at each of 3, 4 and 5 players: 144, 192 and 240 blocks. Six matched arms:
   all authored; focal champion; champion plus responder; adapted champion plus
   responder; focal immediate-only; the highest-ranked distinct spatial plan
   from placement training (excluding authored and refusal). Thus 3,456 held-out games and 1,296 search
   games. Seed prefixes are disjoint across search, counter, adaptation and
   confirmation. No post-confirmation retuning or second champion selection.
   A `--smoke` run uses disjoint smoke prefixes and two blocks per stage only;
   it checks execution, cannot select plans for the full study, and is archived
   separately without qualification authority.

Changing choices can change later random draws and decision counts. Seeds fix
the exogenous deck/board/Audit streams, not identical downstream trajectories.
Publish paired outcomes and do not claim strict per-draw correspondence.

## Direct geography sensitivity

Use the first 48 four-player confirmation blocks. From the champion/ordinary
arm, locate the first rival Facility build with an alternative of the same
district category, Agent, action bundle and actual costs on a different tile.
Replay the whole match forcing only that one legal placement. Prefer the most
distant alternative, tie by decision ID. If none exists, record no opportunity;
do not inject infrastructure or fabricate an observation.

Compare subsequent focal location choices by Era/cycle/stage, final score,
fractional win credit, and final connected Facilities/Ventures. The branch
preserves the rival's immediate costs and district effects. Downstream effects
are real consequences, not an isolated proof of the precise winning mechanism.
Retain the forcing receipt and first differing focal choice. Different legal
choices with identical scores alone are insufficient evidence of useful depth.

## Measures, gates and uncertainty

Record winners, fractional tie credit, all scores and resources, connected
Facilities, active Ventures, per-seat choices, action counts and forced no-ops.
Measure plan win credit and scores, champion gain over authored/immediate-only,
responder own gain and champion suppression, and focal recovery through
adaptation. Report by count, backend and ecology; do not use a thin-cell maximum
to claim dominance. Keep faction/seat strata available in raw outcomes.

For the primary four-player held-out tests publish bounded Hoeffding intervals
for eight preregistered paired win-credit effects, with Bonferroni family alpha
0.05 and support [-1,1]. Paired score means and unadjusted normal intervals are
secondary descriptive diagnostics. Wide intervals fail closed; absence of a
detected exploit does not qualify a mechanic. Uncertainty is over the registered
seed population with rotated factors, not all possible players or strategies.

Practical effect hypotheses use the existing balance contract: best-response
gain 0.18, counter recovery 0.04, holdout collapse 0.20, pairwise dominance 0.70.
They remain hypotheses. The standalone spatial study cannot promote the game.
Also run the existing unified frame with 480 matches, counts 3/4/5, initial two
runs per cell, batch size two, both Mandate modes and its bounded adversarial
slice, on this committed source. Preserve its precision and non-promotion verdict.

The primary gates are: a legal rival-placement branch changes a focal location
and final score; champion-versus-immediate-only lower win-credit bound > 0;
counter own-gain and champion-suppression lower bounds > 0; adaptive-recovery
lower bound >= 0.04; alternative-minus-champion lower bound >= -0.18; and
champion-minus-authored upper bound <= 0.18. These thresholds are hypotheses,
not validated human meaningfulness cutoffs. Publish all six gates without
collapsing them into a favorable average. If any is missing, report **not established**.
Even a positive bounded result is conditional counterplay evidence, not a proof
against every strategy. Experienced human play and independent stronger policy
classes remain separate required evidence before balance qualification.

## Surface audit

- Engine: correct public Venture offer context; no mechanical rule change.
- Browser: show the same offer terms to the human responder.
- UI copy: sourced dynamic offer description, no public balance claim.
- Tests: public information, clearing on accept/reject/failure, actual legal
  blocking and public-only power prediction against the engine.
- Rules, components, physical kit, reference aids, faction starts, costs and
  default policies: no mechanical change.
- Release: new executable and synchronized generated artifacts; historical
  releases remain immutable.
- Balance/playtest documentation: record the result and remaining evidence
  after execution; do not replace pending human observations with simulation.
