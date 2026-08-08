# NNCP/Endpoint Common-Raw-Block Route QM0

## Question

The exact mature NNCP trace loses to Endpoint428 overall on raw bytes
`6,757,802..8,991,577`. Does it nevertheless win persistent local regimes
large enough to justify a two-substrate block representation?

## Frozen construction

NNCP's 16-bit symbols and Endpoint's WRT bits are different coded objects and
their probabilities must not be mixed. Both reversible alphabets are instead
mapped onto identical raw boundaries. Starting at raw byte `6,757,802`, each
block targets 65,536 raw bytes and closes at the first later boundary present
in both alphabets. Both model states remain continuous from byte zero.

The causal arm selects NNCP for the current block only when NNCP beat Endpoint
on the immediately preceding block; the first block uses Endpoint. Each block
pays eight framing bytes. A matched control rotates the loss signal by seven
blocks before applying the same route. A truth-aware block oracle pays the
same framing plus one selector bit and is reported only as a ceiling.

## Gate

Promotion requires at least 20,000 qbit-equivalent causal bytes after framing,
positive gain in every chronological third, at least 5,000 bytes over the
rotated control, complete common-boundary coverage, exact trace and inverse
identity, and a diagnostic source package no larger than 65,536 bytes.

A pass authorizes a separately frozen finite dual-codec container. It does not
grant score credit: the container must terminate each block exactly, update
both decoder states from reconstructed raw data, count both source closures,
and prove roundtrip, determinism, memory, and runtime. A miss retires this
block size, lag, framing, and route without rescue sweeps.
