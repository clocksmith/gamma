"""2767. Partition String Into Minimum Beautiful Substrings: partition by binary values that are powers of five and reject leading zeros."""


def solve(s: str) -> int:
    """O(n * n) time and O(n) auxiliary space on the stated binary-length domain; inputs are read-only."""
    powers = set()
    value = 1
    while value < 1 << len(s):
        powers.add(value)
        value *= 5
    best = [len(s) + 1] * (len(s) + 1)
    best[0] = 0
    for start in range(len(s)):
        if s[start] == '0' or best[start] > len(s):
            continue
        value = 0
        for end in range(start, len(s)):
            value = 2 * value + int(s[end])
            if value in powers:
                best[end + 1] = min(best[end + 1], best[start] + 1)
    return best[-1] if best[-1] <= len(s) else -1


class Solution:
    def minimumBeautifulSubstrings(self, s: str) -> int:
        return solve(s)
