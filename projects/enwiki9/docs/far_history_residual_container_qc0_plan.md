# Far-History Residual Container QC0

## Purpose

QM1 proved the exact collective ledger cost but did not materialize the
residual stream or inverse. QC0 freezes QM1's 584,693 commands unchanged and
seals the substrate-independent transform required before any backend test.

## Format and inverse

The compressed QM1 ledger contains three canonical ULEB128 columns: literal
gap, backward source distance, and copy length. The residual is the canonical
1G input with each selected copy target removed. Decoding consumes each literal
gap from the residual, copies the declared span from already reconstructed
output, then consumes the final residual tail.

Every command must be exact, strictly prior, fully closed, and within the
canonical input. The residual must contain exactly `1,000,000,000 - 64,526,086`
bytes. A second derivation hashes the same literal ranges independently. The
inverse must consume the residual exactly and reproduce canonical enwik9's
SHA-256.

Large residual and reconstruction artifacts live under
`/home/x/enwiki9-nonproof/results/`; the tracked decision binds their paths,
sizes, and hashes. The decoder source is packaged deterministically and must
not exceed 32,768 compressed bytes.

## Cross-substrate boundary

At the published NNCP v3.3 archive rate, QM1's copied population has an
optimistic net proxy of about 3.58M bytes after its ledger and implementation.
That arithmetic would place NNCP's externally reported total below 105M, but
it is not credit: the CUDA stream is not reproduced locally, CPU/GPU streams
differ, runtime eligibility is unresolved, and residual compression may differ
from average rate.

A QC0 pass authorizes only a separately frozen backend integration with an
actual residual archive, counted ledger and source, exact inverse, deterministic
replay, memory receipt, and runtime receipt. QC0 itself earns zero score and
does not change any forecast.
