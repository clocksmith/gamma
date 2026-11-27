# Archive Format `B1RA` (BITS Horizon-Sizing Random-Access Archive v1)

This file is the complete wire specification. `independent_decode.py` is written from this
specification alone and imports nothing from the encoder or sizing harness.

An archive stores an ordered list of `F` byte records (files) with self-contained header,
random-access per-record framing, and zero-drift byte accounting.

## Layout

| Section | Part | Bytes | Meaning |
| --- | --- | --- | --- |
| Header | Magic | 4 | ASCII `B1RA` |
| Header | Entry count | varint | `n`, number of dictionary entries (`n >= 0`) |
| Header | Dictionary | `sum(1 + len(e))` | For each entry `0 <= i < n`: 1 byte length `L` in `1..16`, then `L` raw bytes. Entries must be distinct. |
| Header | Code table | `n + 2` | One byte per symbol: bit length in `1..255` for entries `0..n-1`, then `ESC` (`n`), then `EOF` (`n + 1`). |
| Framing | Record count | varint | `F`, number of records (`F >= 0`) |
| Framing | Record length index | `sum(len(varint(p_j)))` | For each record `0 <= j < F`: varint byte length `p_j >= 1` of record `j`'s coded payload. |
| Payload | Coded records | `sum(p_j)` | Concatenation of `F` byte-aligned record bitstreams, record `j` occupying exactly `p_j` bytes. |

The **header** (`H_K` bytes) is fixed per `(chain, K)` from the fitting corpus before any
calibration or evaluation lineage is seen.

The **body** (`B_K = framing_bytes + payload_bytes = len(archive) - H_K`) stores the record count,
per-record framing index, and coded record payloads. No trailing bytes are allowed past the end of
record `F - 1`.

## Varints

Unsigned integers stored 7 bits per byte, least-significant group first. Every byte except the last
has bit 7 (`0x80`) set. Encodings must be canonical (minimal length: no trailing `0x00` byte on
multi-byte varints).

## Symbols and Canonical Prefix Code

There are `n + 2` symbols:
- `0 <= s < n`: dictionary entry `s`.
- `s = n`: `ESC` (escape), followed in the bitstream by 8 raw bits (MSB first) representing one
  literal byte.
- `s = n + 1`: `EOF` (end of record).

Code lengths `L[0..n+1]` must each lie in `1..255` and must satisfy exact Kraft equality:
```
sum_{s=0}^{n+1} 2^(max(L) - L[s]) == 2^(max(L))
```
This guarantees a complete, prefix-free canonical code tree. Any code table violating exact Kraft
equality or producing duplicate codes must be rejected.

Canonical assignment: sort symbols by `(L[s], s)`. The first symbol receives code `0` of length
`L[order[0]]`. Each subsequent symbol `s` receives `(prev_code + 1) << (L[s] - prev_len)`.

## Record Payload Bitstream

Within record `j` (`p_j` bytes, read MSB-first within each byte):
1. Decode canonical codes sequentially:
   - `s < n`: append `entries[s]` to record output (1 token).
   - `s == n` (`ESC`): read the next 8 bits MSB-first as one byte and append it (1 token, 1 escape).
   - `s == n + 1` (`EOF`): terminate record `j` (not counted as a token).
2. After `EOF`, the remaining bits in record `j` must be strictly fewer than 8 (`0..7` bits) and
   every remaining padding bit must be `0`. No extra bytes may remain inside the `p_j`-byte record.

## Random Access

After reading the header and the `F` record lengths `p_0, ..., p_{F-1}`, record `j` starts at byte
offset `payload_start + sum_{t < j} p_t` and spans `p_j` bytes, so any single record can be decoded
directly without decoding earlier records.

## Accounting Identities (0 B Drift Required)

- `header_bytes = 4 + len(varint(n)) + sum(1 + len(e_i)) + (n + 2)`
- `framing_bytes = len(varint(F)) + sum(len(varint(p_j)))`
- `payload_bytes = sum(p_j)`
- `body_bytes = framing_bytes + payload_bytes`
- `complete_bytes = header_bytes + body_bytes == len(archive)`
- `r_hat_K = body_bytes / source_bytes`
- At horizon `M` bytes: `J_K(M) = H_K + M * r_hat_K`, compared with exact rational arithmetic and
  breaking exact ties strictly toward the smaller header `H_K` (then smaller `K`).
