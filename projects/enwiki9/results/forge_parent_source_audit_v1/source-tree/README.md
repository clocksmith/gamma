# forge-cmix — Hutter Prize submission (enwik9)

forge-cmix is a lossless enwik9 compressor in the cmix → fx2-cmix lineage
(Kaido Orav, GPL), with the fxcm_v26 model family as integrated by cmix-lex
(Ibrahim Marcouch). The name fx3-cmix is intentionally NOT used: it refers to
Kaido Orav's own unpublished follow-up work.

- This project's changes: `MODIFICATION-RECORD.md`
- Algorithmic description: `DESCRIPTION.md`
- Exact build instructions: `BUILD.md`
- Attributions and license texts: `THIRD-PARTY-NOTICES.md`, `licenses/`
- Deterministic file manifest: `SOURCE-MANIFEST.tsv`
- Upstream README (historical, contains outdated numbers): `docs/README-upstream-fx2cmix.md`

## Submission result

    L (current official baseline, fx2-cmix) = 110,793,128 bytes
    cmix   (compressor executable)          =     462,290 bytes
    archive9 (self-extracting archive)      = 109,079,791 bytes
    S = 462,290 + 109,079,791               = 109,542,081 bytes
    1 - S/L = 1.1292%

    sha256(cmix)     = d11595b697a3a932c343aabb16171d289fa2dc2b4e1d3423234e9fe7a88294fd
    sha256(archive9) = 3fea5770bda262650734b6705fa1cda8c5b4f1f7d4eab645c3a6ccf5ed95c90c

## Commands evaluated for the submission

    ./archive9

The self-extracting archive takes no options. It restores
`enwik9_uncompressed` (1,000,000,000 bytes) in the
working directory, sha256
`159b85351e5f76e60cbe32e04c677847a9ecba3adc79addab6f4c6c7aa3744bc`
(bit-identical to enwik9). Temporary files (`ppm.temp`, dot-files) are created
in the working directory; peak disk usage ~21 GB.

The compressor invocation is:

    ./cmix -e enwik9 out.comp

It builds the compressed stream and constructs `archive9`. Both executables
and their resource use are part of the submission evaluation; `archive9` is
the required no-input restoration command.

## Measured on the test machine

Intel i9-10900K @ 3.70 GHz (single core used), 64 GB RAM,
NVMe SSD 1.8 TB, Ubuntu 24.04.4 LTS, kernel 6.17.0-35-generic.
Geekbench 5 single-core score: 1478 (evidence bundle contains the result).

    compress:   164,895 s -> 164,895/3600*1478 = 67,698.6 < 70,000
    decompress: 166,024 s -> 166,024/3600*1478 = 68,162.1 < 70,000
    peak RSS:   8,951,992 KiB (compress), 8,790,176 KiB (decompress) — both < 10 GB
    lossless:   restore verified by byte compare and sha256

Transparent huge pages: the binary calls `madvise(MADV_HUGEPAGE)` on its own
large anonymous mappings (compiled in, see `MODIFICATION-RECORD.md`); it runs
correctly if THP is unavailable (status markers are written to stderr).

## License

GPL — see `LICENSE`. All inherited file headers remain intact; see
`THIRD-PARTY-NOTICES.md` for the complete attribution set.
