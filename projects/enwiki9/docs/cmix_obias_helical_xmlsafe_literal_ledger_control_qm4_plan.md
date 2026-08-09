# QM4 literal-ledger attribution control

This control keeps the frozen 250,000,000-byte QM4 original and the exact
249,407,080-byte residual unchanged. It replaces the copy ledger's source
distances with the 592,920 exact removed literal bytes, while retaining the same
target gaps and lengths. Both ledgers use finite self-delimiting formats and the
same LZMA extreme wrapper.

The literal ledger is decoded and used to reconstruct a materialized 250M
prefix. The reconstruction must match the frozen original SHA-256. Since the
backend residual is identical, the compressed ledger difference isolates the
value of the far-history source relationship without another `cmix-obias` run.

This is an attribution control only. It does not establish a backend gain,
full-corpus transfer, counted package score, runtime eligibility, or the 105M
target.
