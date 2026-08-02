# NNCP v3.3 CPU T16 archive-identity Q0

Candidate: `nncp_v33_cpu_t16_archive_identity_q0_v1`

## Question

Can the immutable source-native LibNC CPU teacher use all 16 physical cores on
this host without changing its bounded archive, and with enough measured
acceleration to justify a complete trace/decode identity gate?

## Frozen run

Use the exact unmodified NNCP v3.3 binary and libraries, the prior opening-1M
raw input, and the prior batch-32 10,000-symbol teacher scope:

```text
-T 16 --profile enwik9 --preprocess 16384,512 --max_size 10000
```

The sole mechanism change from the adjacent reference is `-T 4` to `-T 16`.
The reference archive is 9,246 bytes with SHA-256
`097102977cbaa563e460ef87bf88af99ae6409a5fa3902198316f0308300ffc5` and
the adjacent mean encode time is `279.797` measured seconds.

## Gate

- exact reference archive bytes and SHA-256;
- active process remains below decimal 10 GB;
- guard terminates normally;
- elapsed reduction is at least 50 percent versus `279.797` seconds.

A pass authorizes one T16 trace-off/trace-on/decode repeat and no mature run.
A miss retires local CPU thread scaling without thread-count, affinity, NUMA,
compiler, batch, or model sweeps. This is execution evidence with zero score
and forecast credit. Forecast remains `109,389,323` bytes and verified full-1G
remains unknown.
