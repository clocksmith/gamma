# Frozen bounded fresh recognition result

The unchanged contradiction candidate returned **16/36 correct answers, two wrong
acceptances and 18 abstentions**, with zero unqualified answers and zero questions.
Both wrong acceptances were materially ambiguous descriptions. Only two of the
four required ambiguity abstentions occurred. **Do not promote this candidate.**
The result fails the required behavior even though all 16 returned known-target
answers passed their 64 query-owned independent checks.

| Fresh kind | Planned / executed | Correct answer | Wrong acceptance | Abstention |
|---|---:|---:|---:|---:|
| Paraphrase | 12 / 12 | 7 | 0 | 5 |
| Sibling variant | 8 / 8 | 3 | 0 | 5 |
| Complete description | 12 / 12 | 6 | 0 | 6 |
| Materially ambiguous description | 4 / 4 | 0 | 2 | 2 |

All 32 known targets appeared in the raw top five. This does not establish
semantic identity: the route still rejected half, and similarity/public example
agreement did not prevent the two ambiguity errors. The stock ambiguity omitted
trade cardinality while explicitly excluding fees/cooldown; the route nevertheless
returned the cooldown source. The rank ambiguity omitted whether duplicates
consume positions; the route returned the ordinary duplicate-retaining source.
These are observed correctness failures. No scoring infrastructure failed.
No output, threshold, grammar, source fact, weight or candidate was changed in
response. These opened cases cannot become fresh confirmation evidence again.

## Freeze and independence

The [pre-author evaluator preseal](evaluator-preseal.json) binds all 95 evaluator
sources, preparation protocol, catalogs and prior 20-test/38-subtest checks before
case authorship. Its SHA256 is
`54d2b1fe7ea2c60f7bd7ffb2d5b0b367b06e0790afe656fec6fd97151d0b2dc2`.
The parent explicitly authorized two isolated roles. `/root/fresh_author` saw only
the 16-target identity/title/tag/difficulty catalog; `/root/fresh_reviewer` saw
indexed requirements/signatures and the author packet, without stored solutions
or candidate feedback. Both had only the permitted instruction context. This is
**agent review, not human review**; foundation-model prior exposure is unknown.
[Review metadata](review-metadata.json) retains actual identities/exposure and
counts. All 36 cases were accepted, seven revised before sealing, none replaced.
The raw original packet, revisions, independent oracles and output audit remain
local and hash-bound. Review helper corrections remain recorded separately.

Main copied and hashed opaque packets without parsing fresh case contents,
verified all original serving bytes and controls, then ran `freeze` before `run`.
The [review seal](seal.json) SHA256 is
`83f12d80d44182289cf73bee4f3a55516a5afad7e9092d05aa275d65578eeda1`.
The [fresh candidate](candidate.json) SHA256 is
`b45dc8d0cebb5dea976360203f172447dbec3365acf35dbea1a927ba338cadf7`;
its serving candidate remains
`11e940fdca16abb0b968bd2459ff60285ed442f77e6c6a1bede9502296f69cfa`.
The frozen [preparation protocol](../../contracts/recognition_fresh_suby_v1.json)
retains its original pending-status text as historical input; this result is the
completion authority. Every public decision was sealed before private checks were
loaded. Expected outputs remained outside the unchanged isolated Linux judge.

## Costs and uncertainty

Recorded wall time through scoring was 34.745 seconds; measured parent
process CPU was 103.691 seconds, sampled process-tree peak RSS 3,220,766,720 bytes,
monitored asset/run disk 1,306,905,788 bytes. Four CPU cores/threads, 8 GiB RAM,
5 GiB disk and 900-second cap stayed unchanged. Parent CPU excludes child process
CPU. These counters precede final bootstrap/report writing and shutdown; complete
process startup-to-exit wall time was not separately measured. Encoder cold
loading was 4.161 seconds, charged to the first route; complete
maximum was 4.838 seconds. Loaded route p50/p95/max was 0.664/1.258/1.626 seconds.
Loaded time subtracts observed cold loading; it is not an independently rerun
warm workload. Independent scoring is outside route time and inside experiment
wall time. No training or download occurred.

[Summary](summary.json) separates all denominators, reasons and costs. Eight
families and all 16 qualified targets contributed; the descriptive family bootstrap 95% interval for returned
correct fraction is 0.341-0.593, and wrong acceptance 0.000-0.121. Small clustered
familiar-family samples and unknown model exposure limit interpretation; intervals
do not cover missing cases or weak tests. Summary publication removes private
failure payload/stderr fields; raw receipts remain local. All 93 completed fresh
files and 208 original control files retained contents and mtimes across a
completed resume with no new inference/judging ([proof](resume-proof.json)).

## Remaining work and boundaries

This reduced 66-entry, 16-qualified-target index has no absent-query test and
cannot satisfy the historical full-catalog 1a gate (18/20, zero wrong, 4/4 absence).
Goal 1b has no agreed final numeric coverage gate, and its mandatory ambiguity
behavior failed here. This is not arbitrary unseen solving or composition evidence.
The original reserved descriptions and protected composition remain unopened.

A future development candidate must represent explicit negative requirements and
required missing distinctions conservatively, including trade count and duplicate
ranking semantics, then freeze before a separately authored unopened confirmation.
Do not relabel this frozen result or tune it into a passing confirmation. The
standalone new composition training proposal remains pending human approval;
no learned composition improvement or 2b result has been demonstrated. The
[existing-trace latency attribution](../typed-lcd-suby-latency-attribution-v1/README.md)
is independent evidence, without new compute or a relaxed gate.

Component: algorithm_solver recognition. Intent preserved; actual wrong answers
are retained and block promotion. No component authority/boundary changed.
