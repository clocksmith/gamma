"""Invalid pre-measurement Fiber-FOSSIL v3 negation design.

V3 is preserved to make the rejected algebra explicit. Its N arm owns an
independent unconstrained symmetric KT state; complementing the donor swaps
correct and wrong counts and therefore mirrors D up to integer rounding.
No v3 candidate was sealed, queued, or measured.
"""

TOTAL = 1 << 16
INVALID_REASON = "independent_symmetric_KT_relearns_complemented_donor_sign"


def kt_reliability(correct: int, wrong: int) -> int:
    value = ((2 * correct + 1) * TOTAL) // (2 * (correct + wrong + 1))
    return max(1, min(TOTAL - 1, value))


def assign(reliability: int, donor_bit: int) -> int:
    return reliability if donor_bit else TOTAL - reliability


def compress(data: bytes) -> bytes:
    raise NotImplementedError("invalid pre-measurement design")


def decompress(archive: bytes) -> bytes:
    raise NotImplementedError("invalid pre-measurement design")
