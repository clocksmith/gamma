# Review and execution receipt

Claude approved freeze9c97a45b7 at2026-10-23T23:23Z after checking matched
matrices, all-row warm-start feasibility, alternating solve order, fail-closed
construction caps and separate exact/full-class versus numerical/pool bounds.
Root and an independent agent reviewed the flow proof and failure behavior.
Ten focused synthetic checks preceded freeze; four later reporting-only checks
are documented in[REPORTING-NOTE.md](REPORTING-NOTE.md).

The approved run launched on cores14/15 at23:23Z with single-thread pinned
Python/NumPy/SciPy/HiGHS,8GiB per worker,600seconds per solve,2,400seconds per
cohort and2,500seconds whole job. It completed in1,210.373seconds. R ran warm
then cold; naming cold then warm. All four calls return feasible timed-out
points, no optimality and zero reported search nodes. No restart or fallback.

Independent replay reconstructs exact parent certificates, complete substring
indexes/bans, bounded pools and immutable sparse model hashes; validates
source/qualification/runtime pins; and replays all1,800packets with exact F/C/N
and storage costs. Warm witnesses equal the seeds: F110,156/94,121. Cold
witnesses, after exact minimum-F re-encoding, have F192,792/173,398. Their raw
solver flow objectives418,322/402,369 are retained separately. No<=10%witness.

Warm R/naming selections28,554/27,099, medians74.5/71,p95199/193 and fractions
48.5781%/44.7323%. Cold selections42,808/39,942,medians112/106,p95312/282 and
fractions55.0364%/53.4124%. Every selected dictionary has zero entries at least
90%of a containing source; one-owner shares are3/249warm,5/256R-cold,6/256
naming-cold. Support counts include singleton/unused entries and do not certify
semantic reuse. Requested compactness costs are fully reported.

The run answers a bounded optimization question. Its timeouts do not establish
restricted-pool optimality or full-class infeasibility. Parent integer bounds
remain−27,266/−28,259. Component intent is preserved; no validation/source
execution, M1/default change, protected access or publication boundary change.
Item23's later qualification failure remains separate from exact parent reuse.
