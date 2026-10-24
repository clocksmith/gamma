# Item66 supplied scalable design

Design only, 2026-10-24, following the theorem record bf698f783 and Claude's
04:23Z approval. Root and independent review precede implementation. No
private inputs, runner, pinning, measurement or grid fitting is authorized here.
Preserve the recorded theorem and existing measured63 files.

## Target and fixed prices

Compute the global all-entry charge on supplied fixed sources, global bans,
original occurrence penalties, original seed/pool and their expected identities.
Reconstruct unchanged53 potentials, q53, L and D. All allowed exact substrings
remain eligible; singleton entries are paid. The new operation is

    G(lambda) = lambda*B + sum_p R_p(lambda)
    R_p(lambda) = max nonoverlapping sum max(q53_o-floor(lambda/m_e),0)
    m_e = all allowed occurrences of e across all supplied source IDs.

Keep exactly the fifteen prices `[0] + [D*2**r for r in range(14)]`. This
choice carries63's fixed family without claiming adequate or optimal coverage.
The selected global charge is the smallest G, ties by the smaller price. Report
all fifteen rows with price, lambda*B, residual sum, total charge, numerator
L-G and exact signed ceiling. A maximum-price winner is not evidence that a
larger price helps. No private feedback may change the family.

The first supplied API explicitly returns `min(T57(k), G)` for all k, matching
the recorded tiny proof. Neither lambda0 nor G alone must dominate57 or63.
Lambda0 equals the all-entry schedule cap, a different identity. Count every
allowed occurrence, including zero q and overlaps. No top-entry truncation.

For a later original-input protocol, the intended headline is explicitly
`min(T61(k), G)`, after fresh forced-owner coverage and61 allocation checks
from the same53/57 proof. This is a separate integration step, not a silent
change to the tiny proof API. Budgets below the coverage floor are null/empty;
retain57-only numerical rows separately if useful. No private61/64 receipts
are proposed. Do not combine q charges from different potentials or universes.
An independently valid bound could instead be compared as a lower bound.

## Production construction

Reconstruct unchanged57 and its50/53 ancestry, charging the full baseline, then
build a separate53 context as63 does. Reuse the immutable63 DepthMap structural
utility, after its exact parent/terminal validations, but implement a new
all-entry traversal. Each source start traverses all depth segments, including
shared groups. For each allowed length, suffix-interval width is the global
m_e; group multiplicity is the number of represented lengths and is not m_e.
Retain globally banned groups in the structural traversal but admit no banned
arcs. Fully banned and internal terminal-prefix cases remain covered.

Compute q53 from the checked potential and use a cache of fifteen quotients
for each distinct m_e. Update every forward residual vector in source order,
with free skips and every allowed arc. Keep separate work counters for shared
and owner arcs, q evaluations, quotient divisions and fifteen-price updates.
Each per-start count commitment hashes all ordered `(end,m_e)` rows. Retain
full forward vectors privately or on supplied invented inputs. Price axes are
lists; canonical normalized digests must survive actual JSON transport.

Lambda0 must equal a freshly reconstructed all-entry unpriced maximum vector.
It also must equal item60's all-entry cap/vector when an independently checked
item60 oracle is supplied in tiny tests. Do not call the owner-only57 vector
an all-entry baseline. Production must check initial zero and every finite
nonnegative schedule shape, alongside its independent recurrence audit later.

## Independent construction and audit

Use the unchanged57 independent baseline and fresh old AC occurrence/potential
context with complete33 partition verification. Prove the full shared catalogue
is exactly the allowed shared set, including singletons, before using it as a
classification authority. Explicitly reconcile its cardinality, representative
membership and structural support; an input pool name alone is insufficient.
Global bans apply to every occurrence, including strings banned by another
source's whole body.

A fresh AC traversal counts all overlapping occurrences of each allowed shared
word across every source. These global counts supply shared m_e. For one-owner
words, numeric Z suffix histograms count all within-source overlaps, as63 did;
checked one-owner support establishes these as global counts. Compare the
old occurrence order/counts and independently accumulated one-owner counts.
Absent catalogue entries may not cause division by zero. The complete entry
classification must partition all allowed endpoints exactly once. During the
endpoint scan, traverse the AC automaton's ordinary trie children from its root
once per start, ignoring failure links for this exact-prefix lookup. A shared
terminal supplies its global count; after the trie path dies, later endpoints
cannot be catalogue words. This avoids constructing a new dense start/end-to-
entry map. The existing old occurrence context remains separately charged.

In one endpoint traversal, compute independent backward residual schedules for
all prices and accumulate every supplied forward recurrence right-hand side.
The audit includes free skips and all shared and owner arcs at every price,
not only caps or sampled positions. Require exact forward vectors, caps,
count-stream commitments and global per-price sums. Reconcile lambda0 with an
independent all-entry unpriced schedule, not57's owner schedule. Full53/57
scientific identities and allocation fields remain checked, with no fabricated
historical vectors where only commitments were retained.

The two methods share the33 structural verifier, ancestral parser/authority and
53/57 baseline machinery. Global counts differ (interval width versus shared
AC totals/owner Z); schedule directions and complete recurrence audit differ.
This is explicit algorithmic independence, not separate source provenance.

## State, costs and tiny acceptance

New schedules and recurrence audit state are O(K*N), K=15. DepthMap is O(G+N),
quotient cache O(K*M), M<=G. The shared catalogue/AC, inherited proof, baseline
contexts, Python objects and serialization cost are additional; do not call
this a whole-process memory bound. No materialized full endpoint graph or
per-price rebuilding of occurrence contexts is planned. New arc work is O(K*A)
for all allowed arcs A, with count construction separately charged. No corpus
runtime extrapolation follows from these expressions.

Focused supplied tests must compare the complete tiny oracle against both
kernels: shared and owner entries, identical separate source IDs, global bans,
zero penalties, overlapping occurrences, terminal-prefix groups, integer and
negative ceilings, empty capacity classes and all fifteen prices. Include
real JSON roundtrip at multi-digit ranks and strict scalar/key rejection.
Deliberately alter an intermediate forward value, a global count commitment,
a shared count, a cap and a price row; the checker must reject each. Verify
K*N positions and K*A arc candidates, separately reporting shared/owner counts.

The recorded strict examples use arbitrary supplied q while the scalable
kernels reconstruct q53; use the tiny oracle with the actual reconstructed q53
for cross-checking. Do not falsely require that the general-q examples be
realizable by the old potentials. Strictness can remain a theorem example
while the supplied q53 fixtures are null.

If the new supplied kernels pass, prepare a separately reviewed invented
measurement using the original two50/53/57 fixtures, fixed inputs and prices,
complete history and no private access. Freeze an explicit whole-process
budget before measurement. Only then design an original-nine-input corpus
continuation and the explicit61 combination, with new guards and freeze.
No new qualification, witness search, decoder, source rewrite, M1 change or
publication boundary follows from this design.

## Independent design review

The independent reviewer found no mathematical or catalogue-completeness
blocker. The exact trie-prefix lookup above addresses a concrete storage risk:
a fresh dense endpoint-to-entry map would contradict the intended additional
state accounting. Unique allowed (group,length) identities, support counts and
complete shared-group cardinality checks establish catalogue completeness.
Root accepts this design for supplied kernels and tiny checks only. A measured
protocol, pending pins and every private-input continuation remain subsequent
review gates.
