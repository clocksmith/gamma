# HELICAL Far-History Corridor QM0

## Question

The frozen full-1G far-history population exactly copies 64,526,086 bytes in
584,693 nonoverlapping matches, but its inline commands cost 4,058,323 bytes
and its collective gap/distance/length ledger compresses to 3,296,268 bytes.
Does the same exact target population admit materially cheaper source-address
trajectories when sources are chosen for corridor continuity rather than age?

## Frozen population

QM0 consumes the exact QM1 raw ledger with SHA-256
`580cca00014f02e425b10692afc33e817259d9ab4b6fcc953201ea48aa5f0cf8`.
It does not change target intervals, the 32-byte rolling window, anchor mask 63,
100,000,000-byte distance floor, 64-byte discovery minimum, maximal extension,
chronological nonoverlap, or collision verification.

For each target, the scanner retains the original earliest source, up to eight
recent eligible sources carrying the same frozen anchor, and exact projected
continuations from the preceding target's bounded candidates. Every candidate
must reproduce the entire frozen target interval byte-for-byte, remain strictly
prior, and be fully closed. The total candidate cap is sixteen.

## Arms

- `M0`: the original tag plus canonical ULEB distance and length. It must equal
  4,058,323 bytes exactly.
- `D0`: QM1's existing deterministic collective LZMA ledger, 3,296,268 bytes.
- `C0`: a minimum-address constant-diagonal path. One full distance opens a
  corridor; equal-diagonal successors pay no new address.
- `C1`: the same candidate graph with either a new full distance or a finite
  signed diagonal shift, whichever is cheaper.
- `CS`: candidate diagonal sets are reassigned deterministically within matched
  length and distance bins. This is a noncodec geometry control and receives no
  reconstruction credit.

`C0` and `C1` serialize exact gaps, command modes, address or shift payloads,
and lengths, then receive one deterministic LZMA command audit. This first gate
does not claim implicit CDC extents; those are authorized only if bounded
corridors survive the finite command and shuffled-control tests.

## Gates and claim boundary

Both complete scans and both command streams must be byte-identical. Every real
candidate must be exact, prior, and closed. `C0` must beat `CS`; compressed `C1`
must beat the 3,296,268-byte existing ledger; and at least one diagnostic parent
inequality must remain positive after the compressed source package and a
500,000-byte reserve.

The Endpoint428 and `cmix-obias` gross values remain average-rate proxies in
this gate. A pass authorizes actual state-preserving selected-span pricing for
each parent independently. It does not update a forecast or earn score credit.
