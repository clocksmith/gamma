# TotalByteEnvelope for BITS packages (`bits-envelope-v1`)

A byte claim about a BITS package is accepted only if it counts every byte a reader needs:
payload, packet framing, dictionary, index and (when charged) decoder. The ordered vocabulary
hash must match too. `envelope.py` measures these from the files, never from a producer's
numbers, and requires **0 B drift**. It uses only the standard library and imports nothing
from Gamma: no `model.py`, no codec and no other checker.

```sh
python3 -B envelope.py /path/to/gamma                    # the four frozen matched80 packages
python3 -B envelope.py --bundle DIR CLAIM.json           # one bundle against one claim
python3 -B -m unittest discover -s . -v                  # 11 tests, a few seconds
```

## The frozen matched80 packages (pin `59ff0441`)

| Job | Records | Payload | Framing | Dictionary | Index | Decoder | Total = `package_bytes` |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `b-w-compact` | 64 | 9,477 | 2,624 | 433 | not stored | 0 | 12,534 |
| `b-u-compact` | 64 | 9,187 | 2,624 | 1,289 | not stored | 0 | 13,100 |
| `c-w-compact` | 80 | 8,190 | 3,200 | 566 | not stored | 1,536 | 13,492 |
| `c-u-compact` | 80 | 2,708 | 3,200 | 15,852 | not stored | 1,536 | 23,296 |

All four reconcile with 0 B drift. Each packet carries a 40- or 41-byte header (magic, the
32-byte dictionary hash and a code count), so framing is 21% of `b-w-compact`. The packages
store one file per program and no index. Their `package_bytes` is therefore reported with
`random_access_total: null`. In one blob with an offset index, `c-w-compact` is
13,492 + 4 × 81 = 13,816 bytes, and that is the figure a random-access comparison must use.

## What is rejected (`test_uncounted_index_or_slot_swap.py`)

The fixtures are the pinned `c-w-compact` packets, concatenated into one records file beside
an index of 81 big-endian uint32 offsets. The honest claim is derived in the test from file
lengths and the fixed header, without calling the checker.

- **Uncounted index:** no `index` field; `index: 0`; the frozen `package_bytes` presented as the
  random-access size; index bytes moved into `payload`.
- **Drift:** a total 1 B below the sum of its components.
- **Unlisted file:** a second dictionary left in the bundle without a role.
- **Bad index:** offsets that are not the record boundaries.
- **Slot swap, claim side:** the fixture of Gamma `06562147d`, two vocabulary slots swapped in
  the claim, same file.
- **Slot swap, file side:** two slots swapped in the stored dictionary (same length), with the
  packets kept. The packets name the old dictionary hash.

Mutation check (2026-11-26): with the index checks removed, 4 tests fail. With the
ordered-vocabulary check removed, the claim-side slot swap fails.

## Scope

This is byte accounting for BITS's own packages. It does not score any codec against zstd or
FSST. The short-record comparison (deco#219) is paused by the owner, and its harness has its
own accountant in `../short-record-byte-accounting-v1`.
