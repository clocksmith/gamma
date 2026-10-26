"""2683. Neighboring Bitwise XOR: require the cyclic xor differences to cancel."""


def solve(derived: list[int]) -> bool:
    """O(n) time and O(1) auxiliary space; inputs are read-only."""
    parity = 0
    for value in derived:
        parity ^= value
    return parity == 0


class Solution:
    def doesValidArrayExist(self, derived: list[int]) -> bool:
        return solve(derived)
