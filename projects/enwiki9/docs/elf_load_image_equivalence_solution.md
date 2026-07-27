# Solution to the ELF Load-Image Equivalence Problem

Status: complete constructive solution
Version: `ELI-1-SOLUTION`

The ELF loader uses the ELF identification and machine fields, entry point,
and program header table. For each mapped segment it uses the header's type,
flags, virtual address, file size, memory size, and alignment, copies the
referenced payload bytes, and zero-fills any remaining memory extent.

Equality of \(\Lambda\) therefore gives equal mapped bytes, zero-filled bytes,
permissions, interpreter request, dynamic segment, auxiliary loader segments,
and entry point. File offsets may differ without consequence because the
payload selected by each offset is compared directly.

With equal initial process image, arguments, environment, shared libraries,
and external inputs, deterministic transition semantics imply equal machine
states by induction. The base states are equal. If states through step \(t\)
are equal, the next instruction and all visible inputs are equal, so states
and side effects at step \(t+1\) are equal. Hence output files and exit status
are equal.

A compressor invocation consequently emits the identical archive, and a
decompressor invocation emits the identical reconstruction. Static symbols,
debug data, and section tables are irrelevant only under the explicit
non-introspection hypothesis.

A finite verifier parses the fixed ELF header and finite program header table,
records the stated fields, extracts each finite segment payload, and compares
the resulting tuples. It rejects malformed bounds, classes, endianness, or
machines.

EPT-1 then applies to any package encoding of \(E'\) and its auxiliary
payloads. Since archive length is unchanged, counted score changes by exactly

\[
P'-P.
\]

The theorem is conditional on the loader and non-introspection model. A native
gate remains mandatory to catch unsupported loader behavior, wrapper errors,
library differences, startup overhead, memory changes, and violations of the
assumptions on the actual submission host.

