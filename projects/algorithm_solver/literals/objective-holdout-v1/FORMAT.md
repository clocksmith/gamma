# Archive format `BOH1`

This is the whole specification. An independent decoder is written from this file alone.

An archive stores a list of files. It is read from the first byte to the last; file boundaries come from the
archive itself. Nothing outside the archive is needed to decode it.

## Layout

| Part | Bytes | Meaning |
| --- | --- | --- |
| Magic | 4 | ASCII `BOH1` |
| Entry count | varint | `n`, the number of dictionary entries |
| Dictionary | sum of `1 + len` | For each entry in order: one byte holding its length (1 to 16), then that many bytes |
| Code table | `n + 2` | One byte per symbol: its code length in bits (1 to 255) |
| File count | varint | `f`, the number of files |
| Payload | rest | The coded files, as a bit string |

The first four parts are the **header**. The header is fixed before any test file is seen. It is the same bytes
in every archive made with that dictionary.

A varint stores an unsigned integer seven bits at a time, least significant group first. Every byte except the
last has its top bit set.

## Symbols

There are `n + 2` symbols. Symbol `i` for `0 <= i < n` is dictionary entry `i`. Symbol `n` is the **escape**. Symbol
`n + 1` is **end of file**. The code table lists their code lengths in that order.

## Codes

Codes are canonical. Sort the symbols by code length, then by symbol number. The first symbol gets the all-zero
code of its length. Each later symbol gets the previous code plus one, shifted left by the difference in length.

## Payload

Bits are written most significant bit first within each byte. For each file, in order:

1. Write the codes of its tokens. A token that is a dictionary entry stands for that entry's bytes. An escape
   code is followed by eight raw bits, most significant first, and stands for that one byte.
2. Write the end-of-file code.

After the last file the bit string is padded with zero bits to a whole byte. A decoder stops after `f`
end-of-file codes and ignores the padding.

## What is counted

| Name | Bytes |
| --- | --- |
| Magic and counts | 4, plus the two varints |
| Dictionary | sum of `1 + len(entry)` |
| Table | `n + 2` |
| Payload | the bit string, rounded up to a byte |
| **Complete** | the size of the archive file |
| Dictionary already held | complete minus the header |

The escape is charged twice: it takes one of the slots a cap allows, and every escaped byte costs the escape
code plus eight bits.

One table serves every file. There is no per-language routing, so no routing bytes.

The format gives sequential access only. The **random-access** figure is a separate count, never mixed with
the complete figure: each file's bits are padded to a byte, and one varint per file stores that file's byte
length. The zstd rows are counted under the same two contracts. Sequential: the dictionary plus one frame per
file, concatenated; a zstd frame ends itself, so no index is needed. Random access: the same plus one varint
per frame.
