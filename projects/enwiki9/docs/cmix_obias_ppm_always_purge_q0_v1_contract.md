# cmix-obias PPM Always-Purge q0 v1

This is a zero-credit infrastructure candidate, not a compression algorithm.
It uses the parent source's existing disk-backed PPM heap and exact
`MADV_DONTNEED` path. The only build change is:

```text
-DCMIX_PPMD_RSS_BUDGET_MB=0ULL
```

The check cadence remains one check per 5,000 input bytes. A zero budget makes
every check purge currently resident pages from the shared `ppm.temp` mapping.
Later faults reload the same bytes from the file/page cache. Table contents,
pointer offsets, context hashes, model updates, probabilities, arithmetic-coder
state, preprocessing, package assets, and decoder behavior are unchanged.

The candidate is accepted only if a matched clean build and this build produce
identical integer probability receipts and payload bytes, two candidate runs
are byte-identical, the bare inverse is exact, all scratch is removed, and
every monitored process tree remains below 9,765,625 KiB. Package delta is
counted even though expected compression savings are zero.

The opening 250KB run is only a build/identity diagnostic and cannot establish
full-corpus memory compliance. Promotion requires a prospectively frozen larger
memory population and finally an isolated full-corpus correction-only replay.
This policy must be composed into any later Gamma compression child before it
can satisfy the campaign resource contract.
