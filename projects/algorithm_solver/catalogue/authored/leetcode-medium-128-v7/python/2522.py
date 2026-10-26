"""2522. Partition String Into Substrings With Values at Most K: extend each decimal piece greedily until the next digit would exceed k."""


def solve(s: str, k: int) -> int:
    """O(n) time and O(1) auxiliary space; inputs are read-only."""
    pieces = 1
    value = 0
    for character in s:
        digit = ord(character) - ord('0')
        if digit > k:
            return -1
        if value * 10 + digit > k:
            pieces += 1
            value = digit
        else:
            value = value * 10 + digit
    return pieces


class Solution:
    def minimumPartition(self, s: str, k: int) -> int:
        return solve(s, k)
