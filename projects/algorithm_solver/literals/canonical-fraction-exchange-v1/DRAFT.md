# Item 47: canonical fraction exchange with per-program seed caps

Design and supplied-input proof only. No runner, binder, freeze, private input or
launch is authorized here. The proposed two cohorts reuse item 40's fixed 300-fit
R/naming sources, exact bounded pools and measured 249-entry seed dictionaries.
No validation or new qualification is proposed. Binding awaits a separate review.

## Question and motivation

Item 44 optimized minimum-F paths, F=10C−N, and found fraction gains. Its canonical
shadow increased total selections by 1,132 for R and 1,167 for naming, with median
increases of 3 and 4.5. That tradeoff does not answer whether fraction can improve
without worsening any source's canonical action count. Item 47 changes the scored
path policy and constrains every program, rather than relying on aggregate gain.
These deltas are in the accepted [item 44 record](../direct-fraction-exchange-v1/README.md)
and [canonical shadow](../direct-fraction-exchange-v1/evidence/canonical-shadow.json),
recorded in 07d99f2f2. Its sorted-subset canonical seed N values are 26,108 R and
24,750 naming; these exact per-ID views, not historical original-order ties, must
bind the later cap vector. Pin both public records before any experiment contract.

For each program p, encode the seed canonically and freeze its selection cap
K_p=N_p(seed). Every retained candidate must cover every source and satisfy
N_p(candidate)<=K_p. This implies nonincrease in every paired action count and
all order-statistic selection/action quantiles relative to the seed. These are
seed-relative caps, not monotonically tightening incumbent caps: a later move may
increase one program from below its cap while still satisfying the original cap.
Report both seed-relative and adjacent-incumbent changes. No average may hide a
seed-relative regression. N counts selections excluding the single Finish action.

## Exact canonical policy and objective

Give the whole bounded pool fixed IDs in sorted-string order. Every dictionary is
a sorted subset. Encode by minimum (N, complete pool-ID sequence), with no C tie
break and no minimum-F path. Dense transmitted IDs preserve relative pool order;
cache word identities or pool IDs, never dense subset IDs that change after moves.
A final packet reassigns dense sorted-subset IDs and reconstructs exact source bytes.

On the occurrence DAG use reverse DP. At each position compare
(1+best_N[end], first_pool_ID). The entry's fixed word and start determine its end;
there cannot be two different suffix states with the same first entry. The retained
suffix is already canonically minimal, proving the complete-sequence tie rule by
induction. Count C only after choosing the canonical path. In particular, two
shortest paths can have different C and canonical encoding can choose the higher C.

Among covered, within-cap dictionaries of at most 256 paid entries, admit only a
strict improvement in (C_total/N_total, N_total, full_package_bytes). Compare the
ratio exactly: C' * N < C * N', with arbitrary-precision integers. On equality,
compare N and then complete package bytes. No floating ratio or averaged per-source
fraction decides admission. Fixed decoder bytes are charged and do not change ties.
All character entries consume capacity and dictionary bytes; no character fallback.
Characters may be removed only if the resulting complete candidate remains covered
and within every cap. Do not restore missing seed characters for convenience.

A strict ratio gain need not lower raw C if N grows inside its seed caps; exact
N/C/fraction and per-program changes remain visible. A strict package or N gain at
equal ratio is an admitted plateau, not a claimed fraction improvement. The seed
has no claim to joint median/p95 feasibility or full-class optimality.

## Exact incremental cache proof

For a move adding A and removing R, recompute every program containing any added
entry anywhere, plus every program whose current canonical path uses a removed
entry. All other paths are exact cache hits. An added entry absent from the source
cannot add an edge. Removing an unused edge leaves the selected canonical path
feasible; deleting competitors cannot make a remaining path beat it. Fixed relative
ID order preserves the lexicographic comparison. The union rule remains valid for
swaps, including when an isolated removal was uncovered or violated a cap.

Replace affected C_p/N_p contributions by exact integer deltas, then compare the
new aggregate ratio by cross multiplication. Caps remain the seed vector and are
checked for every affected row; unaffected rows inherit checked validity. Dictionary
storage changes for all moves even if no path changes. A final full canonical
rescore must match all cached paths, N/C, ratio and package before retention.
Independent reporting later uses a separate sliced-string/full-sequence reference
DP and packet decoding, never the search cache or minimum-F paths.

## Fixed opportunities and non-exhaustive scope

Retain item 44's procedure as a structural control: fill at most the seed's seven
free slots with complete single-addition sweeps; then bounded exchange epochs.
Each epoch starts from one immutable incumbent: score all absent pool entries,
all current-entry removals, and top-four addition candidates crossed with every
current-entry removal. Addition ranking at full capacity may temporarily contain
257 entries, but cannot be accepted or serialized. Its canonical fraction score
is a heuristic ranking only, not a lower bound on a repaired swap's ratio.
Rank by exact (ratio,N,package), then fixed added pool ID. No removal is omitted
because its standalone trial is uncovered or violates a cap; every shortlisted
joint swap is directly evaluated from the immutable incumbent. A new incumbent
only starts after choosing and fully rescoring a strict winner from the sweep.

Freeze each phase's opportunity list/hash and cardinality before evaluation,
including the addition shortlist and full Cartesian swap order. Count every probe,
coverage/cap failure and retention rescore against the same evaluation budget.
Record attempted/completed/recomputed rows, separate coverage/cap violations,
interrupted trial, sweep completeness and omitted opportunities. Deduplication,
if used, must be declared and preserve an explicit map to original opportunities;
no silent filtering from failed singleton probes. Ties among strict winners use
fixed dictionary pool-ID sequence after the objective, not a mutable history.

Adopt item 44's partial-sweep rule: a bounded partial sweep may retain only a
winner already fully rescored by the search-side scorer within both the search
and whole-job budgets. This is a cache check, not the independent reporter
algorithm; that separate replay is required before acceptance of the final record.
A partial sweep cannot establish no improving neighbor or local optimality.
A whole-job failure never promotes a checkpoint. No decision based on corpus
runtime is permitted. Top-four ranking itself leaves many swaps untested;
even a complete sweep is not exhaustive dictionary search.

## Legality, costs and evidence boundary

Rebuild item 40's exact bounded pool from its pinned inputs and compare identities,
seed entries and all global full-source/solve-body bans. Preserve its pool cap and
one-million-arc and 20-million-trie-transition construction caps; fail closed
without truncation. Pool support,
one-owner and near-whole shares are reported, not treated as semantic reuse proof.
All source contents remain unchanged and exact qualification hashes inherited.
No whole-body entry, free escape, source rewrite, validation choice or private case.

The later comparison reports both seed/final canonical policy on the same 300 IDs:
all N_p<=K_p, fraction, C, N, selections/actions quantiles, packet/dictionary/framing/
padding/full decoder costs, exact changed-per-ID counts, support/entry lengths,
phase budgets and retained/rejected opportunity counts. The old minimum-F witness
may appear only as a labeled historical comparator, never as the optimized policy.
This remains a one-owner/full-substring relaxation on bounded pools, not an M1
candidate, default promotion, 400/500 exclusion or full-class infeasibility claim.

## Proof and complexity work before a budget proposal

Synthetic checks must exhaust small dictionary subsets and direct moves against
an independent enumerator, prove canonical ties can differ from min-character and
minimum-F choices, reject per-source cap violations even when total N falls,
accept a feasible swap whose standalone removal was uncovered, preserve exact
ratios with integers beyond floating precision, and validate cache/full-rescore
identity after additions/removals and subset renumbering.

Measure an invented full opportunity sweep including all addition rankings,
all removals, all top-four swaps, cap checks, exact ratio comparison and a complete
winner rescore. Pin prototype/test/measurement/interpreter hashes before running.
Report graph size, source lengths, completed and failed opportunity counts, time
and peak memory. No budget or corpus runtime forecast is selected before that
measurement. No production runner, input binder, freeze or launch in this task.


## Invented proof results and proposed bounded follow-up

Six supplied-input tests pass (0.024 seconds): exhaustive tiny dictionaries and
all single additions/removals/swaps; canonical higher-character ties versus
minimum-F; per-program cap rejection despite lower aggregate N; an uncovered
standalone removal repaired by a joint swap; exact ratios beyond floating-point
precision and secondary ties; and randomized cache/full-enumerator agreement.
One initial test invocation used the repository directory and could not import
the test module; the corrected directory invocation ran all six. No test corpus
or experiment input was opened.

The measurement spec was written before execution and pins the prototype, tests,
measurement code and resolved interpreter, plus the verified parent 44 contract
and its 144 frozen code/10 runtime pins. The three measured Python files remain
immutable for interpreting this receipt. One invented fixture uses 300 strings,
75,000 characters, maximum length 400, 2,048 pool entries and a 249-entry seed.
It is the same disclosed random-text fixture as item 44, not real source input.
The graph has 188,961 occurrence arcs and 263,211 trie transitions.

| Probe | Completed evaluations | Coverage failures | Cap failures | Program recomputations |
| --- | ---: | ---: | ---: | ---: |
| Addition | 1,799 | 0 | 0 | 41,600 |
| Removal | 249 | 14 | 233 | 27,539 |
| Top-four joint swap | 996 | 56 | 932 | 204,706 |
| Winner full rescore | 1 | 0 | 0 | 300 |

Coverage failures and cap failures are disjoint here: uncovered trials stop before
cap assessment. There are 3,044 declared move opportunities and 3,045 total
completed evaluations including the rescore. Failed standalone removals do not
filter the swap product. The seed has C=3,332, N=39,166 and full package 65,962;
the selected winner has C=3,150, N=39,075 and full package 65,872. All 300 seed caps
hold. These artificial ratios are not evidence toward the corpus 10% target.

Graph construction took 0.163 seconds; the complete sweep and rescore took 47.019
seconds; whole guarded measurement took 48.252 seconds. Peak RSS was 144,040 KiB.
Core 4, 8 GiB, 55-second signal guard and outer 60-second timeout plus 5-second
kill-after were used; execution exited 0. See [specification](synthetic-spec.json)
and [measurement](synthetic-results.json). This establishes feasibility of this
invented sweep only, with no extrapolated corpus ETA or parameter tuning. The
measurement performs exactly one final-winner rescore. A production wrapper must
fully rescore each newly best proposal before it becomes retainable, as item 44
does, and charge all those rescores; its work can therefore exceed this fixture
even with the same move count. Preserve the measured code byte-for-byte and add
time checks in a new wrapper, not by rewriting this measurement.

Propose the same finite production envelope as item 44: seven free-slot sweeps,
then at most twelve exchange epochs; all additions and removals, top four swaps;
600 search seconds and 50,000 attempted evaluations per cohort, including every
winner rescore. Use cores 4/5 when root schedules them, one thread and 8 GiB per
worker, 1,200 seconds for whole production and a separate 1,200 seconds for
independent replay, with separately bounded ten-second process-group cleanup.
Timing tests for that later wrapper must cover early coverage and cap failures
as charged attempts, and interruption during a new-best full rescore. An expired
rescore cannot replace the last already fully checked incumbent.
The two phases must use fresh output folders and include setup, input/pool checks,
output and failure publication in their hard guards. The measured mechanism does
not justify increasing these limits to force a result. Keep parent construction
caps of one million arcs, twenty million transitions and two million pool characters.

Retain only an already fully search-rescored improvement if the soft search budget
interrupts a sweep; report every omitted opportunity. A hard phase failure or
independent replay failure yields no accepted witness and no retry. The proposed
budget allows an intentionally incomplete neighborhood search, not a promised
number of completed epochs. No production code, binder, freeze or launch is part
of the present task; root/Claude review is still required for any such work.
