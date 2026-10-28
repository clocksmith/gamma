# Batch four independent source-exposed qualification

This lane owns only the 46 problem pairs delivered in
`authored/downloaded-general46-v1`. It preserves their exact original source bytes.
Neither author-reported tests nor cross-language agreement count as independent
qualification. Historical protected Gamma source/case datasets are not inputs.

The local contract checks the supplied functional `solve` interface: unchanged
arguments, full typed result and fresh mutable output containers. These effects
are an explicit local service envelope. They are not a claim that the official
problem requires fresh returns. In particular, problem 406 can satisfy the
official queue predicate while failing this local alias envelope. Its original
implementations retain input row objects in their result.

For problem 443 the local adapter returns the compressed character vector.
Official example lengths are checked against the length of that vector. This
does not qualify the original `Solution.compress` wrapper: it fails the required
input mutation and new-length return ABI. That interface failure remains a
mandatory gate. Problem 442's input-sized count maps fail its mandatory constant
auxiliary-memory bound even if the output values pass. Optional follow-ups for
419 and 457 are not silently converted into mandatory algorithmic gates.

`oracles.py` implements independent expected results, using bounded enumeration,
graph reachability, complete output predicates, multiset cover and direct game
models. `cases.py` checks newly generated domain facts, validates references
against public official examples, includes exhaustive small cases, seeded cases
and legal maximum-size witnesses with separately derived results. Large witnesses
are isolated into their own interpreter batches. Most random cases are small;
finite checks do not prove behavior over every legal input. The reference tests
cross-check less direct algorithms and wrong-value/type/effect/alias controls.

Public official definition responses are privately retained and hash-pinned.
44 contain public statements. Definitions 408 and 418 are unavailable behind the
official premium boundary. New local cases for those two are marked prepared;
their definition gate remains failed, regardless of execution outcomes. No hidden
case acquisition or access bypass is used.

Only the original source, observation transport and argument packet enter the
existing isolated Linux judge. Expected results stay on the host. Exact sources,
interfaces, functional adapter, helpers, definitions, runtime and resource limits
are frozen before execution. One interpreter at a time uses at most a 1 GiB
address-space limit, three CPU seconds and eight wall seconds. Jupiter had
87,995,572,224 bytes available at the initial memory check. Public contribution
services are not stopped. Source archives and frozen hashes, rather than the
executor's unrelated working-checkout revision, identify tested code.

Raw streams and process metadata are saved before judging. The separate replay
regenerates expectations and checks every raw digest and observation. Original
failures remain; any repaired variant requires a different source identity and
new freeze. These results do not automatically promote catalogue entries,
qualify retrieval, or establish official judge acceptance.
