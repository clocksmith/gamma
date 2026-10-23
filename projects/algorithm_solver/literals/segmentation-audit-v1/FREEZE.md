# Exact segmentation and character-tail audit

Board16, goal2a. The existing shortest encoder resolves equal selection counts
by lower first dictionary ID. A minimum-selection path can therefore use more
single-character codes than another equally short path. This measurement-only
stage isolates segmentation choice from dictionary/source limitations. No previous
packet, canonical encoder, readiness verdict or M1 threshold changes.

## Fixed inputs and four exact objectives

Use item13's hash-bound control128/control256, scope256 and scope_joint256 sources
and dictionaries on the same allowed fit300/validation100. All400 sources per
seed already qualified under item13; reuse those exact source-hash-bound receipts.
The two scope seeds and especially scope_joint's selection were informed by
consumed development outcomes; this is adaptive analysis, not fresh generalization.
No held-out100/protected66 is read. No corpus segmentation measurements precede
this freeze; four synthetic tests include150 exhaustive tiny path comparisons
under each policy, tie cases, a character/action tradeoff and an unencodable case.

For each fixed source/dictionary, run exact backwards DAG dynamic programming:

- `canonical`: minimize (selections,0), then lexicographic dictionary-ID sequence.
  Assert its sequence equals the current canonical encoder, and its counts match
  the published item13 receipt.
- `shortest_min_char`: minimize (selections, single-character codes), then IDs.
- `shortest_max_char`: minimize (selections, negative single-character codes),
  then IDs. This bounds the tie range at minimum selections only.
- `min_char`: minimize (single-character codes, selections), then IDs. This is
  an exact absolute-character minimum witness, which may require more selections.
  It does not minimize character fraction and is not a fraction lower bound when
  the denominator is allowed to increase.

No source rewrite, dictionary fitting, model, search-cap heuristic or case feedback
occurs. For fixed source, all four sequences decode through the unchanged flat
literal decoder. Preserve sequences privately; publish hashes/counts only.
Independently decode all6400 packets. Assert shortest policies have identical N,
min_char N>=minimumN, and min_char C<=shortest_min_char C<=canonical C<=shortest_max_char C
for every source. Source/dictionary whole-solution legality and qualification
are hash-bound reused evidence, not freshly re-executed cases.

## Costs and scope

Report fit and validation separately: selections/actions distributions, <=32/96,
absolute character counts and fraction, per-program tie gains, paired counts,
dictionary/packet/framing/padding and raw/decoder-inclusive packages. One Finish
per program. All characters share each seed's fixed7/8-bit width, so code fraction
is payload-bit fraction; framing remains separately charged. Canonical dictionary
format and decoder do not change. The alternate encoders are offline research
policies with tooling bytes charged separately; complete runtime footprint is
unmeasured. Any candidate encoder promotion would need a new freeze/review.

Predictions:

- T1: canonical fully reproduces each seed's source, sequence and N/C counts;
  all6400 independent decodes pass and objective inequalities hold.
- T2: shortest_min_char reduces validation absolute character codes by at least5%
  versus canonical for control256, with exactly unchanged selections/actions.
- T3: min_char reduces control256 validation character codes by at least10% versus
  canonical, while increasing its aggregate actions.
- T4: no policy/seed meets every M1 cost indicator on consumed validation.

There is no new source/dictionary input-candidate readiness selection. Report
these objective witnesses even when existing5%action readiness cannot apply.
A lower single-character fraction alone does not establish human fluency, search
optimality over dictionaries, autonomous composition or M1. The shortest_min_char
witness proves the minimum fallback fraction only at fixed minimumN for these
exact sources/dictionaries. No impossibility claim beyond that restricted problem.

One CPU worker on core8,1GiB address-space and600-second overall ceiling. Freeze,
code and contract pushed then Claude review (or PLAN30-minute timeout) before
measurement. Rebuild reports separately. Component intent preserved; no production
boundary or canonical codec change. Training, protected opening, publication,
BITS deployment, independent confirmation and human study remain owner-gated.
