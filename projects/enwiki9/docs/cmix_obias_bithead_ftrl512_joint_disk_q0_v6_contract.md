# FTRL512 Joint Decision v6

This is a correction-only decision successor over the frozen v5 C/P/K/O/R/D/S
arm artifacts. It changes no compressor source, corpus, probability, adapter,
package, or resource boundary and grants zero compression credit.

v6 adds the receipt checks missing from v5:

```text
K shadow gate maximum > 0
K shadow logit maximum > 0
finite = true for encode 1, encode 2, and bare decode
q hash identical across encode 1, encode 2, and bare decode
recurrent state hash identical across all three executions
adapter hash identical across all three executions
gate and logit maxima identical across all three executions
```

All existing gates remain mandatory: exact roundtrip and repeat, C=P payload,
P=K probability/state/payload, D smaller than P/K/O/R/S, live O/R/D/S controls,
non-memory-backed scratch, allocated scratch from zero through
100,000,000,000 bytes, process-tree RSS at most 9,765,625 KiB, and incremental
required program material at most 65,536 bytes.
