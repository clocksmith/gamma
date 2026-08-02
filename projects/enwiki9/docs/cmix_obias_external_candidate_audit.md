# cmix-obias external candidate audit

Status: unverified external self-report; zero Gamma score credit; code donor,
not an adaptive proposal or queue entry

Audit date: `2026-08-02`

## Claimed result and evidence boundary

The public `dfreelan/cmix-obias` artifact describes a Hutter submission derived
from `cmix-lex`. Its `SUBMISSION.md` reports:

```text
archive9                              108,009,834 bytes
compressor binary                       459,989 bytes
separate bit-head weights                 23,002 bytes
claimed counted total                 108,492,825 bytes
claimed raw scope                   1,000,000,000 bytes
claimed archive SHA-256  664823c5d9f167bda342745d7b34a3ccb98fd7108723ba83643d9d09bf693900
```

The same document reports a byte-identical full decode, but no Hutter committee
announcement or independent terminal verification was located. This audit did
not download and run the 108 MB archive. Treat every result as an external
self-report, not a record, teacher certificate, or Gamma source-bound fact.

The reported peak RSS values are `10,420,896 kB` for compression and
`10,438,000 kB` for decompression. Interpreting Linux maximum-RSS units as KiB,
they are respectively `655,271 KiB` and `672,375 KiB` above Gamma's strict
decimal-10GB guard of `9,765,625 KiB`, although they remain `64,864 KiB` and
`47,760 KiB` below binary 10 GiB. The official disposition of those units is
not inferred here.

Primary public artifacts:

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `SUBMISSION.md` | `5,306` | `c53a335189d3dfdab2971b570bf96cd5b9e64fa1131b7736881f114c202a4390` |
| `BITLSTM32_SPEC.md` | `7,561` | `c1b26a150e0742a51b8d3c95839ffc1e40f35762de02b1a18184b811abc1cb8c` |
| `obias-prior.cpp` | `11,502` | `04fec966da1d0d889a895f09a0b67d662d5568b937d6992ee425558bed6ff0b9` |
| `obias-prior.h` | `2,905` | `f2adc3a9bbe7766e5ff5fb23ff4fede5d6bfc29686ce07d8283c47283fa0b953` |
| `bitlstm32-head.cpp` | `24,059` | `e0593d64bef9323467d838724f926bb32efdcaef957afd48a14ff318577ff77f` |
| `bitlstm32-head.h` | `2,697` | `7d84d9c9445125a92fd8e8d0e10dfa2f7a1333866a4312cdc39fb6ac40702926` |
| `refit_golden256_fp16.blob` | `23,002` | `35cd24fed87c3409994abf5573b5697be19ea03b5ece0928b69b1cdc4f3b6078` |

Source: `https://huggingface.co/dfreelan/cmix-obias`, whose submission document
identifies source snapshot `60c499e`.

## Contingent prize arithmetic

This self-report does not change the still-listed official record or Gamma's
standing `108,000,000` design target. If `108,492,825` were accepted as the
record, however, the maximum integer score satisfying a subsequent one-percent
improvement would be:

```text
floor(0.99 * 108,492,825)           107,407,896 bytes
Gamma forecast distance               1,981,427 bytes above
108,000,000 target distance              592,104 bytes above
108,000,000 improvement over record          0.4542466%
```

Therefore `108,000,000` would still set a smaller record but would not meet the
minimum one-percent prize claim after this hypothetical reset. Track
`107,407,896` as a contingency only until authoritative verification exists.

## Mechanism audit

The external implementation combines four changes:

1. A 256-cell byte LSTM, enlarged from its `cmix-lex` parent and paid for by a
   separate speed campaign.
2. `bitlstm32`, an 11,489-parameter, 64-bit-reset recurrent logit correction
   head serialized as 23,002 fp16 bytes. Its 92 causal inputs include internal
   expert logits, multiscale residual and surprise windows, relative expert
   losses, eight preceding bytes, and absolute corpus-position features.
3. `obias`, a fixed `g=0.15` addition of the log PPMd next-byte distribution to
   the byte-LSTM output logits while retaining the existing PPMd auxiliary
   input. The deployed constant gate needs no model blob.
4. Output-neutral CPU, memory-mapping, PGO, LTO, and packaging changes.

`bitlstm32` is not the retired CHIRON construction. CHIRON used a 143,711-
parameter two-layer GRU over completed WRT bytes, reset every 256 WRT bytes,
without the mature mixer's internal expert row, multiscale realized-surprise
state, or exact corpus-position geometry. It is closer to the terminal JANUS
fixed-corpus residual family, but the external feature source and 64-bit reset
are materially different.

The supplied attribution remains too small to interrupt the current queue. The
submission document estimates about `530 KB` full-stream gain for the residual
head and reports `4,837` bytes for `obias` at 50 MB, approximately `96.74 B/M`.
Neither independently clears Gamma's `3,000 B/M` gross admission screen. The
complete claimed improvement over the submission document's `cmix-lex`
reference is about `1.157 MB`, but it mixes LSTM width, two probability
mechanisms, speed work, packaging, parent differences, and full-corpus
selection. Those gains cannot be transferred or added to Gamma.

## Disposition

Retain `cmix-obias` as a zero-credit external code donor and competitive-risk
receipt. Do not reopen a blind LSTM-width sweep, CHIRON, or JANUS unchanged.
Do not interrupt NNCP or the WIKIBACK/WIKISECTION/WIKIFORWARD/WIKIGRAPH
sequence.

If a predictive-substrate slot opens, the smallest attributable transplant is
one frozen `g=0.15` PPMd output-prior control against endpoint428, with the
existing PPMd auxiliary input retained and a symbol-permuted PPMd distribution
as the specificity null. A separate rich-state residual-head ceiling would
first require an exact endpoint428 internal-expert trace and must charge its
model twice under the applicable Hutter packaging form. Neither experiment is
authorized by this audit, and neither receives forecast credit without an
actual native archive and full ledger.
