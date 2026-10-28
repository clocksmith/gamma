# New repaired source identities

The original 92-source baseline and its frozen contract remain immutable. This
revision changes only separately stored variants for 406, 418, 433, 442, 443 and
502, in both languages. `sources.json` pins originals and repaired bytes.

406 clones each returned person row. 433 returns zero for an already identical
start/end gene before requiring bank membership. 502 uses a max heap rather than
repeatedly sorting/removing from a list of affordable projects. 418 jumps through
the periodic sentence instead of placing every word separately; its primary
definition gate remains unavailable and cannot be waived by successful cases.

442 uses constant auxiliary memory, excluding the returned duplicates. It marks
input positions temporarily and restores every original value in `finally`.
This requires exclusive mutable access during the call; it is an unchanged-on-
return postcondition, not an immutable-input promise. The official problem allows
input mutation. Any consumer requiring immutable input must use another adapter
and account for its memory separately.

443 retains a functional fresh-vector `solve` entry and separately implements
the official `Solution.compress` in-place/new-length interface. Decimal digits
are emitted through scalar divisor state, not a separate digit array. The native
wrapper has a separate adapter and host comparator: return value must be an
integer length, and the mutated input prefix must equal the independently
computed compressed vector. The ignored tail is not over-constrained.

Both the repaired and original 443 wrappers execute through the same native
adapter. The original is a negative control that must be rejected, rather than
being counted as a passing implementation. The Python observation transport
selects the packet entry without rebinding the candidate's global `solve`.

All 12 repaired variants receive the same cases, bounds, expected results and
resource caps as the original baseline. No cap or definition requirement is
relaxed. Exact repaired source and adapter bytes, helper hashes, runtime and
batch plans are frozen before execution. Promotion and consumer integration
remain outside this owned lane and require root review.
