"""2840. Check if Strings Can be Made Equal With Operations II: compare character counts separately for even and odd positions."""


def solve(s1: str, s2: str) -> bool:
    """O(n) time and O(1) auxiliary space for the lowercase alphabet; inputs are read-only."""
    counts = [0] * 52
    for index, (left, right) in enumerate(zip(s1, s2)):
        offset = 26 * (index % 2)
        counts[offset + ord(left) - ord('a')] += 1
        counts[offset + ord(right) - ord('a')] -= 1
    return all(count == 0 for count in counts)


class Solution:
    def checkStrings(self, s1: str, s2: str) -> bool:
        return solve(s1, s2)
