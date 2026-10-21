# Shared heap refactor under frozen dictionaries

One semantic source refactor reduces Last Stone Weight (#1046) from **494 to
205 eight-bit selections (58.50%)**, using the **unchanged** 256-entry dictionary.
Across the same 100 development problems, total selections fall **7,374 → 7,085
(3.92%)** and the package falls **14,086 → 13,797 bytes**.

[Contract](contract.json) · [Source lineage](generated/manifest.json) ·
[Execution](qualification/report.json) · [Matched comparison](summary.json) ·
[Complete winning source](generated/sources/1046-heap-role.js) ·
[Exact sequence](encodings/heap-role-8/manifest.json) ·
[Exact strings](encodings/heap-role-8/dictionary.json)

## The reusable piece

The previous solution carried a separate priority-queue class and its methods.
The new implementation uses an array heap and the exact **133-byte sift-down
helper** already used by #976 and #1051. Dictionary entry **209** now supplies
that same helper to a third problem. All guard, copying, control-flow and helper
source bytes remain explicitly encoded; decoding performs no substitution.

After removing the maximum, the second-largest value is at the root. Replace it
with their nonnegative difference and restore the heap. Equal stones may leave a
zero, which cannot change subsequent positive-stone outcomes; every iteration
still removes one array element. Heap initialization is linear, repeated updates
are logarithmic, and storage remains O(n). This is an algorithmic complexity
argument, not a newly measured maximum-input speed or memory result.

The original safe-integer/domain guard and JSON-copy behavior are retained.
Input arrays remain unmodified. This source was deliberately refactored offline;
no neural composer or query-time source generator selected it.

## Results

| Same 100 problems | Before | After |
|---|---:|---:|
| Eight-bit selections | 7,374 | **7,085** |
| Complete package | 14,086 B | **13,797 B** |
| Median / p95 selections | 62 / 152 | 62 / 152 |
| Worst program | 494 | **230** |
| Character selection bits | 52.22% | 52.59% |
| Seven-bit selections | 12,478 | **11,997** |
| Seven-bit complete package | 16,411 B | **15,990 B** |

The single #1046 packet costs **246 bytes**, including its 41-byte header;
its 205 selections carry 1,640 payload bits. The complete shared dictionary still
costs 2,612 bytes. At seven bits, #1046 improves from 775 to 294 selections.

**332/332 checks** passed across the original control and three source candidates,
using the same **83 distinct independent development cases** and exact original
output/input-effect parity. **206 packets** were independently decoded and checked
by a separate forward segmentation routine. The other 99 programs reuse their
qualified source receipts. No additional independent-case coverage is claimed.

Absolute character selections fall, but their fraction rises because total
selections fall faster. The refactor improves the expensive tail; it does not
improve median/p95 or satisfy Milestone 1. No whole-solution entries were added.
Protected sets, recognition and corpus admission remain untouched.

## Reproduce

The execution wrapper uses the existing Linux sandbox and unchanged cases.
Source generation and qualification require fresh output directories; preserve
the recorded evidence. The measured source files, dictionary and packet are public.
Full 100-program packages include earlier private inputs and stay on 128 at the
private_full100_packages path in summary.json.

To decode the single public packet, use the existing bitpack.py API with
encodings/heap-role-8/dictionary.ltd and encodings/heap-role-8/1046.ltv.
The full comparison is implemented in measure.py; it requires the hash-matching
private 100-problem pool and a fresh private output path.

Next: apply the same approach to shared dynamic-programming rows, windows and
backtracking structure. Compare genuine code reuse against the frozen naming-only
baseline; keep all runtime arguments and source choices counted.
