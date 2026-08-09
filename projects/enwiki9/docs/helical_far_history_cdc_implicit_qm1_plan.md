# HELICAL Far-History Implicit CDC QM1

## Question

QM0 proved real but insufficient address amortization. Its diagnostic columnar
command streams cost 3,175,732 bytes, including 751,080 compressed target-gap
bytes and 445,292 compressed byte-length bytes. Can the frozen rolling anchors
make target placement and copied extent decoder-visible cheaply enough to
recover that tax without changing the exact source universe?

## Frozen construction

QM1 consumes QM0's deterministic `C1` stream with SHA-256
`2f35bfe0d84f14a82f6e47aba4a810fcf5a1f71a0eea08391456adb071487e1f`.
It rebuilds the original 32-byte, mask-63 rolling anchors across canonical
enwik9. For each frozen target span, only complete anchor-to-anchor chunks are
eligible. Edge bytes remain literal. The corresponding source start and end
must both be frozen anchors, the complete chunk range must compare equal, and
the source must remain at least 100,000,000 bytes earlier and fully closed.

The target schedule is transmitted either as one bit per decoder-visible chunk
or as paid ULEB literal-gap/copy-count columns. The smaller actual deterministic
LZMA representation wins. Address modes, full openings, signed shifts, framing,
and the complete compressed source package are independently counted. No byte
length or raw target offset is transmitted.

## Gate

Two complete scans and every raw command column must be byte-identical. Copied
coverage must be positive in every corpus third. The implicit command package
must beat the 3,175,732-byte columnar QM0 diagnostic. At least one independently
priced diagnostic parent inequality must remain positive after its debt, the
complete command/source cost, and a frozen 500,000-byte reserve.

A pass authorizes archive-identical selected-span instrumentation against that
parent. Average-rate gross values are not score credit and cannot update the
forecast. A miss retires this mask-63 implicit-chunk realization without a CDC
mask sweep.
