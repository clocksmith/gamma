# Item63: entry-price owner path caps

Proof-only refinement of item57. Charging at most λ per used owner entry leaves a residual interval schedule; taking the minimum of these affine bounds and original activation prefixes preserves concavity and cannot weaken57.

The [derivation](DRAFT.md), [explicit oracle](proof.py) and [exhaustive tiny tests](test_proof.py) use supplied nonnegative integer penalties and a finite integer lambda family containing0. They neither load corpus data nor choose prices.

A constructed coverable k1 example lowers the charge20→17 and raises the integer bound−4→−1. It demonstrates strictness on general fixed q, not positive certification, q53 strictness, optimal prices or corpus gains. Six focused tests passed in0.112 seconds. See the [review record](REVIEW.md).

No scalable implementation, private input, benchmark, binder, pending contract, execution or promotion is authorized. Items60/61/62 remain separate mechanisms.

## Supplied implementation design

The [fixed-family design](DRAFT-NEXT.md) uses15 globally declared integer prices, laminar suffix-group occurrence counts in production and independent per-start Z histograms. Every price schedule and forward recurrence must reconcile. Root and independent review found no design blocker against the actual33 Index. Supplied kernels and tiny correctness checks may now be implemented; a separate reviewed invented measurement remains necessary before any corpus design. No private input or run is authorized.

## Supplied kernels and independent replay

The [production kernel](caps.py) walks laminar depth segments and prices every
allowed one-owner arc; the [independent checker](independent.py) derives
multiplicities with per-start Z histograms and fresh AC ownership. Both
reconstruct57 and charge their additional potential/index context. All15 fixed
prices, lambda0 full-vector identity, finite allocations and JSON-stable
scientific digests agree on tiny supplied populations.

Eight production tests passed0.167seconds, including actual JSON-to-checker
agreement at capacities0/1/16/256; five independent tests passed0.270seconds.
Both handle separate and aliased one-shot ban iterables. Root and read-only
independent audit found no blocker; syntax/import checks pass. The checker can
run without supplied vectors for tiny standalone analysis; any measured paired
run must supply both57/63 forward schedules and verify every recurrence and
its checked flag/digest. These are development checks, not complexity evidence.
A separate fixed-fixture measurement protocol is being prepared; no private
input, timing run or corpus contract exists yet.

## Accepted invented measurement

The [single fixed-fixture measurement](SYNTHETIC-RESULT.md) completed in137.054628
supervisor seconds with19oracles and all49code/12runtime commitments unchanged.
Paired75k is null at all257 budgets. Repeated12k improves65 raw/integer budgets,
including k3 28459→29587, but k*=4 and fullk256−151368 stay unchanged. All price
and historical schedule checks pass. No original-fit gain or runtime forecast
follows; a separate original-input design is next.

The grid's top is8192000000 in penalty units. It is a per-entry price; division
by an entry's occurrence count gives the per-occurrence subtraction. It is not
a claim to span every useful price or zero every residual. Public57 maximum
owner path caps bound single-occurrence q and average W_e/m_e by8892964810R/
7934232825naming. Thus the grid top covers that loose average upper bound for
naming, but this argument cannot establish it forR. These public aggregates do
not tightly bound m_e*max(q), which suffices to zero all of an entry's residuals.
The family stays fixed; no pre-freeze private probe or grid adaptation is implied.
