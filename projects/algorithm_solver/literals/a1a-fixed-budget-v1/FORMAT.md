# Archive Formats `A1AF` (Flat Literal) and `A1AD` (Construction DAG)

This specification defines both self-contained archive formats for BITS Experiment Card A1a.
An independent decoder (`independent_decode.py`) is written from this specification alone and
shares no code with the encoder (`headers.py`).

Both formats serialize the same fixed emitted vocabulary of `n` distinct entries (each 1 to 16
bytes), the same canonical Huffman code table for `n + 2` symbols (`0..n-1`, `ESC = n`,
`EOF = n + 1`), and the same bit-packed payload for `f` files. Every byte needed by the
recipient is inside the archive (`complete_bits = 8 * len(archive)`).

## Primitives

- **Varint:** unsigned integer encoded 7 bits per byte, least-significant group first. Every byte
  except the last has bit 7 (`0x80`) set. Canonical minimal encoding is required (no redundant
  trailing `0x00` continuation byte when value > 0).
- **Bit packing:** MSB-first within each byte. Any unused padding bits at the end of a bit-packed
  section must be fewer than 8 and all zero (`0`).
- **Canonical Huffman codes:** `n + 2` code lengths in bytes (each `1..255`). Sort symbols by
  `(length, symbol_id)`. The first symbol gets the all-zero code of its length; each subsequent
  symbol gets `(prev_code + 1) << (length - prev_length)`. The Kraft sum
  `sum(2^(max_len - l))` must equal `2^max_len` (exact complete prefix code).

## Format 1: `A1AF` (Flat-Literal Header)

| Part | Bytes | Meaning |
| --- | --- | --- |
| Magic | 4 | ASCII `A1AF` |
| Entry count | varint | `n` (`n >= 1`), emitted vocabulary entries |
| Dictionary | sum of `1 + len(e)` | For each entry `0..n-1`: 1-byte length (`1..16`), then raw bytes. All entries must be distinct. |
| Code table | `n + 2` | Canonical Huffman code length per symbol (`0..n-1`, `ESC`, `EOF`) |
| File count | varint | `f`, number of files |
| Payload | rest | Canonical Huffman bit stream for `f` files, zero-padded to whole bytes |

## Format 2: `A1AD` (Construction-DAG Header)

| Part | Bytes | Meaning |
| --- | --- | --- |
| Magic | 4 | ASCII `A1AD` |
| Flags | 1 | Bitfield: bits 0..1 = `mode` (`0` = pure-pair DAG, `1` = hybrid DAG; `2,3` invalid); bit 2 (`0x04`) = `has_emit_mask`; bit 3 (`0x08`) = `has_merge_ranks`; bits 4..7 must be `0`. |
| Total DAG nodes | varint | `M` (`M >= 1`) |
| Leaf count | varint | `A` (`1 <= A <= 256`, `A <= M`) |
| Leaf bytes | `A` | Strictly ascending single-byte leaf values for DAG nodes `0..A-1` |
| DAG node table | bit-packed, byte-aligned | Definitions for nodes `i = A .. M-1` (see below), zero-padded to whole byte boundary |
| Merge ranks (optional) | bit-packed, byte-aligned | Present iff `has_merge_ranks` and `M > A` (see below) |
| Emit mask (optional) | `ceil(M / 8)` | Present iff `has_emit_mask`. Bit `i` (LSB-first in byte `i >> 3`) is `1` iff DAG node `i` is emitted. Unused high bits in the final byte must be `0`. At least one bit must be `1`. |
| Code table | `n + 2` | Canonical Huffman code lengths for the `n` emitted symbols (in ascending DAG node order), then `ESC = n`, `EOF = n + 1`. |
| File count | varint | `f`, number of files |
| Payload | rest | Identical canonical Huffman bit stream to `A1AF`, zero-padded to whole bytes |

### DAG Node Table

For each non-leaf node `i` in `A .. M - 1`, let the dynamic parent index width be
`w_i = max(1, (i - 1).bit_length())` bits (minimum bits to represent `0 .. i - 1`).

- **`mode = 0` (pure-pair DAG):**
  Read `left` (`w_i` bits) and `right` (`w_i` bits). Both must satisfy `0 <= left < i` and
  `0 <= right < i`. The node string is `dag[left] + dag[right]`.
- **`mode = 1` (hybrid DAG):**
  Read a 2-bit tag:
  - `00` (pair): read `left` (`w_i` bits), `right` (`w_i` bits); require `left < i`, `right < i`;
    string is `dag[left] + dag[right]`.
  - `01` (literal): read 4-bit `len_minus_1` (`length = len_minus_1 + 1`, require `2 <= length <= 16`),
    then `length * 8` raw bits.
  - `10` (list): read 4-bit `cnt_minus_2` (`cnt = cnt_minus_2 + 2`, require `2 <= cnt <= 16`),
    then `cnt` node indices of `w_i` bits each (every index must be `< i`); string is the
    concatenation of those nodes.
  - `11`: invalid (`FormatError`).

Every non-leaf node `i` must produce a string of length `2..16` that has not appeared at any
earlier node `0..i-1`. Trailing padding bits at the end of the DAG node table must be `< 8`
and all zero.

### Optional Merge Ranks (`has_merge_ranks = 1`, `M > A`)

Let `R = M - A` and `rw = max(1, (R - 1).bit_length())`. Read `R` unsigned integers of `rw` bits
each, zero-padded to a byte boundary (padding bits must be `0`). The values `rank[0..R-1]` must
form an exact permutation of `0..R-1`, and for every node `i >= A` referencing non-leaf children
`c >= A` (pair or list children), every such child must satisfy `rank[c - A] < rank[i - A]`.

## Payload Decoding

Read canonical Huffman codes MSB-first from the payload bit stream until `f` `EOF` symbols have
been decoded:
- `0 <= sym < n`: append `emitted[sym]` to the current file.
- `sym == n` (`ESC`): read the next 8 bits MSB-first and append that single byte.
- `sym == n + 1` (`EOF`): emit the current file and start the next.

After the `f`-th `EOF`, remaining trailing bits must be `< 8` and all zero.

## Random-Access Accounting

Sequential `complete_bytes` is `len(archive)` (`complete_bits = 8 * len(archive)`).
Random-access `random_access_complete_bytes` adds per-file byte padding and one length varint per
file: `header_bytes + len(varint(f)) + sum(ceil(b / 8) + len(varint(ceil(b / 8))) for b in per_file_bits)`.
