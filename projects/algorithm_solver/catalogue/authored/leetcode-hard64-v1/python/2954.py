"""2954. Count the Number of Infection Sequences: interleave healthy gaps and count internal infection directions."""


def solve(n: int, sick: list[int]) -> int:
    """O(n + log MOD) time and O(1) auxiliary space. Inputs are preserved."""
    modulus = 1_000_000_007
    healthy = n - len(sick)
    # Accumulate factorial products modulo MOD rather than constructing huge integers.
    numerator = 1
    for value in range(2, healthy + 1):
        numerator = numerator * value % modulus
    denominator = 1
    exponent = 0
    previous = -1
    for index in range(len(sick) + 1):
        position = sick[index] if index < len(sick) else n
        gap = position - previous - 1
        for value in range(2, gap + 1):
            denominator = denominator * value % modulus
        if 0 < index < len(sick) and gap:
            exponent += gap - 1
        previous = position
    return numerator * pow(denominator, modulus - 2, modulus) % modulus * pow(2, exponent, modulus) % modulus


class Solution:
    def numberOfSequence(self, n: int, sick: list[int]) -> int:
        return solve(n, sick)
