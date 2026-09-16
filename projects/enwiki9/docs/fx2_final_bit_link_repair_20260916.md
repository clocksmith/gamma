# Linkage correction for the final-bit experiment

Version1 stopped at the linker before any corpus encode. The observer header
included a non-inline SHA implementation in four translation units. The old
head observer had been included in only one. The original syntax checks passed
because they did not link these units together. Preserve that failure.

Version2 inserts only the C++ `inline` specifier before the unique SHA function
definition. All original bytes, including CRLF and notices, otherwise remain
unchanged. It uses a new source path and adapter; the measured v1 stays intact.
The learner, audit wrapper, rounding, projection, feature map, delayed control,
population, resource ceilings and17-phase comparison are unchanged.

An independent three-translation-unit reproducer fails with the original header,
links with the corrected one and matches Python's SHA256 of `abc`. This resolves
the demonstrated linkage defect. It establishes no model or archive improvement.
The original synthetic/calculus checks remain bound; the correction has a new
linkage receipt. Version2 still needs the entire native comparison.

[Failure](../operations/provenance/fx2_final_bit_build_failure_20260916.json),
[repair test](../operations/provenance/fx2_final_bit_link_repair_20260916.json),
[unchanged scientific design](fx2_final_bit_head_20260916.md).
