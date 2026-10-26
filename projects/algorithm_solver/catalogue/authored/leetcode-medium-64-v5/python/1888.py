"""1888. Minimum Number of Flips to Make the Binary String Alternating: slide an n-character window over the implicit doubled string."""


def solve(s: str) -> int:
    """O(n) time and O(1) auxiliary space; inputs are read-only."""
    length = len(s)
    mismatches = 0
    best = length
    for right in range(2 * length - 1):
        mismatches += ord(s[right % length]) - ord('0') != right % 2
        if right >= length:
            left = right - length
            mismatches -= ord(s[left % length]) - ord('0') != left % 2
        if right >= length - 1:
            best = min(best, mismatches, length - mismatches)
    return best


class Solution:
    def minFlips(self, s: str) -> int:
        return solve(s)
