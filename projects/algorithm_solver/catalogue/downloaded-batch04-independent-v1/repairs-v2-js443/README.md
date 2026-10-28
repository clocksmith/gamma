# Actual JavaScript named String Compression interface

The prior executed v1 source proves `Solution.compress`, while its named
`compress = solve` alias returns a new compressed array. That class proof does
not establish the official JavaScript standalone `compress(chars)` interface.
This new source changes only that alias to `compressInPlace`; prior source,
frozen contracts and raw observations stay unchanged.

The primary official 443 snapshot, starter bytes and metadata pin the named
function, integer return, argument-zero mutation and output prefix of returned
length. The native comparison checks exact integer length, prefix and actual
argument prefix. The remaining tail is unconstrained. The changed source's
`compressInPlace` loop writes only prior/current positions, uses two cursors and
a constant-size count-digit generator; no input-sized auxiliary buffer or
recursion is used. Digits are emitted by division and modulo over count <=2000.
The free functional helper deliberately retains fresh-array semantics.

Four separate units execute: actual new named entry, old v1 named alias negative
control, new class compatibility, and new free solve. Independent existing 443
cases and expected results are reused, never cross-language agreement. Raw
observations bind exact source, adapter, interface, helpers, runtime and limits.
Only source, argument packets and observation transport enter the isolated judge;
expected results remain on the host. One interpreter at a time uses 1 GiB address,
three CPU seconds, eight wall seconds and bounded output, without service changes.
Requested slots, completed observation rows and complete interpreter streams are
reported separately. A missing complete row does not prove whether its call began.
This evidence does not establish production service execution or catalogue promotion.
