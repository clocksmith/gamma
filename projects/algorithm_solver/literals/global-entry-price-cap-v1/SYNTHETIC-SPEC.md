# Item 66 proposed supplied-input complexity protocol

2026-10-24. Root approved the design and authorized the new harness and focused
harness tests. This specification describes that implementation; it authorizes
no pin generation, measurement, private access or corpus continuation. Preserve
the recorded theorem, supplied kernels and all measured ancestors. Code review,
reviewed public pins and separate launch authority remain required. No retry is
implicit in any failure.

## Fixed invented inputs and price family

Use the two original item 50 fixtures in their exact order:
`paired_prefix_75k` (300 sources of 250 characters, seed 50065), then
`repeated_one_owner_12k` (12 sources of 1000 characters, seed 50112).
Retain the original generator, bans, 96-character alphabet, sorted complete
shared pool, seed, original integer q generation and occurrence order,
D=1000000, B=256. The unchanged input-spec SHA256 is
`a7d7843c947ccf0d8c691086614379cd5ddaa5f918bc50602e7947847f446f25`.
No adaptive resizing, selected population, q adjustment, warmup on these
fixtures, preliminary timing or private probe is permitted.

The globally fixed fifteen prices are exactly
`[0] + [D * 2**r for r in range(14)]`. Evaluate every price on both fixtures.
Each entry denominator counts all globally allowed occurrences, shared and
one-owner, including overlaps and zero-q occurrences. No endpoint, entry or
price is truncated to improve runtime. Retain every global price charge
`lambda*B + sum_p R_p(lambda)` and its exact signed ceiling. Choose the smallest
charge, with the smaller price breaking ties. Return the explicit same-q
`min(T57(k), G)` for every k=0..256. This measurement does not insert item 61's
required-owner rule or any item 60/62/64 constraint.

The price range is a fixed choice, not an adequacy claim. A maximum-price winner
does not establish that a larger price helps; an interior winner does not prove
global optimality. Lambda0 is the all-entry unpriced schedule, not item 57's
owner-only schedule. Item 63 supplies an immutable structural utility, but no
item 63 numerical result or timing ratio is a comparator in this protocol.

## Historical authority and immutable closure

Before fixture work, verify accepted item 57 synthetic spec, result and
supervisor, both complete receipts, strict integer zero exit, absence of
failure markers, finite bounded historical clocks and all comparison flags.
Verify its full pinned code/runtime closure and inherited accepted 50/53
public metadata. Bind the immutable item 63 `DepthMap`/helper dependency and
its measured closure explicitly; reusing that code does not rerun its kernel
or treat its numerical results as an independent baseline.

The builder reconstructs only public invented metadata to verify
the original input digest. It must not construct a pool/q or call kernels.
Its measured-file inventory must be explicit, including these design files,
the tiny proof/tests, new production/checker/tests, the new harness/tests,
and this specification. Explicitly include `joint-path-cap-v1/proof.py`, which
the registered oracles dynamically import to check the all-entry unpriced
identity; it is not in the inherited item 63 measured closure.
Future README/REVIEW files or corpus wrappers must not
silently change an existing inventory. The exact measured closure is frozen
and pushed before the single measurement; pin construction alone is not run
authorization.

Reconcile each realized fixture's source/ban metadata, pool count/bytes/hash,
original q hash/count/order and generator transitions against accepted 57.
Reconstruct its entire 50/53/57 science from the same supplied inputs. Compare
fresh production and independent common 57 fields, complete paired 53 proofs,
all historical 50/53/57 rows and all recorded scientific/top/prefix/schedule
commitments. Preserve historical production and independent directional
commitments separately. Where only a historical hash was retained, compare the
new full values between kernels, then that hash; do not fabricate a historical
vector. Exact original path terms, L/D, geometry, class counts and original
certificate identity are required, not just headline bounds.

## Work inside the single clock

All imports, public preflight, all registered small oracles, fixture construction,
pool/q generation, baseline and additional contexts, both new kernels,
comparison, serialization, process cleanup and publication are charged to the
same absolute deadline. The current oracle inventory is **20** tests: 7 proof,
8 production and 5 checker. The harness loads and checks that actual
inventory, runs it before fixture phases, and reports its time separately while
keeping it inside the whole budget. Harness fault tests remain focused
development checks rather than recursively measured tests.

Production reconstructs unchanged 57 and a separate 53 potential/index context.
It uses immutable 63 `DepthMap`, traverses all allowed owner and shared depths,
and reconstructs a separate unpriced vector from q53. The checker reconstructs
unchanged independent 57, fresh old AC occurrence/order/potential/support
identity and the complete shared catalogue. Shared denominators use fresh AC
global counts; one-owner denominators use numeric Z overlap counts. An ordinary
trie walk per source start resolves shared terminals without a new dense
endpoint map. All duplicate baseline construction, catalogue/index work,
quotient caches, Z work and serialization remain charged and disclosed.

Supply the full production 57 vectors, all fifteen price vectors, unpriced
vectors, shared counts, count commitments, caps and price rows to the checker.
It builds backward price and unpriced schedules and audits every production
forward recurrence. Require all corresponding checked flags and exact vector
hashes. Compare lambda0 with the complete independently reconstructed unpriced
vector in both directions; never substitute the 57 owner cap.

For K=15, total source characters N and allowed all-entry arcs A, verify K*N
new price-forward positions and N unpriced-forward positions. Check K*A
production, backward and audit price candidates, plus A production, backward
and audit unpriced candidates. Check A q evaluations and complete count records,
K*N price skips, N unpriced skips, exact shared/owner partition of A, and
quotient-division/cache counters. Baseline 57 recurrence and work identities
remain separate. Work accounting is exact integer arithmetic, not a runtime
prediction or whole-process memory bound.

Compare all new common fields and canonical digests: every shared catalogue
ID/global count; each per-start `(end,m_e)` count stream hash/count; every price
and unpriced cap; all fifteen price rows including entry charge and residual
sum; selected index/global charge; all 257 combined rows and raw/integer gains.
Canonical hashing normalizes inherited integer keys and tuples before sorted
JSON encoding and rejects key collisions/scalar substitutions. Actual retained
JSON roundtrip is a required focused regression. Directional vectors differ;
validate their commitments and complete recurrences rather than equating them.

## Retained evidence and interpretation

Retain input/ban/pool/q/occurrence identities, all 50/53/57/66 curves, per-k raw
and integer deltas, all fifteen price rows, selected index/global charge,
shared counts, count-stream commitments, price/unpriced caps, scientific and
schedule hashes, all separate baseline/new work counters, phase times and peak
RSS. Large vectors may be committed and fully replayed without copying them
into the final public result. Invented numeric tables can be retained; this
provides no authority to publish later corpus owner arrays or entry identities.

Missing either fixture, skipped price, failed oracle, historical mismatch,
corrupt count/cap/vector, partial recurrence or resource overrun means incomplete
with no accepted complexity comparison. A new strict gain is evidence only on
these invented q53 inputs. General-q theorem toys do not predict its sign. A
nonpositive bound remains inconclusive. There is no optimized q, optimum price,
corpus runtime estimate, timing ratio, new witness, source execution,
qualification, M1, validation or protected-input claim.

## Bounded lifecycle

Adapt the accepted item 63/60 lifecycle without changing those files: one
**600-second** absolute whole-job clock, core 6, one numerical thread, and
**8 GiB address space per process**. Start the clock at initial import and arm
the bootstrap guard before research imports. Pass that same deadline into a
fresh isolated worker process group; phases cannot refresh it. Peak worker and
supervisor RSS are separate measurements; cumulative worker peaks are not
incremental per fixture and do not establish an aggregate 8 GiB cap.

Normal cleanup and success publication finish within the original deadline.
Cleanup is additionally bounded by ten seconds from its start. Failure receives
one absolute emergency deadline, at most first-failure+10 and original-deadline+10.
Failure during normal cleanup retains that cleanup's original start. Kill all
worker descendants before potentially blocked unlink, wait, log close or
failure publication; every subsequent operation checks only the remaining
absolute allowance. No swallowed hard deadline may resume unguarded I/O.
An eventual root external **610-second** guard is backup, not extra successful
computation time.

Fresh output is required, and rejecting an existing output must leave it
unchanged. For an output created by this attempt, withdraw complete markers
before fallible failure writes. Publish success only after group cleanup,
with prose preceding receipts and complete results last. Both complete
receipts, exact reviewed spec identity and absence of failure are required for
acceptance. Normal Python assertions are mandatory. Focused harness tests must
exercise real descendants, timeout/worker failure, blocked cleanup/failure I/O,
partial publication, existing-output preservation and tiny complete JSON flow.
The harness is implemented under the separate root authorization. No pin or
fixed-fixture run is authorized by this specification.
