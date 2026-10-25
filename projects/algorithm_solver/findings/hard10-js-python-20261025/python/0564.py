"""564. Find the Closest Palindrome (Hard).

Fresh candidate authored in this conversation; no repository solution copied.
Specification: https://leetcode.com/problems/find-the-closest-palindrome/description/
Canonical API: solve(n); also exposes Solution.nearestPalindromic.
Inputs are preserved. Gamma independent qualification is pending.
"""

def solve(n: str) -> str:
    length = len(n)
    value = int(n)
    half_length = (length + 1) // 2
    prefix = int(n[:half_length])
    candidates = {10 ** (length - 1) - 1, 10 ** length + 1}

    for delta in (-1, 0, 1):
        adjusted = prefix + delta
        if adjusted < 0:
            continue
        half = str(adjusted)
        if len(half) != half_length:
            continue
        reflected = half[:-1] if length % 2 else half
        candidates.add(int(half + reflected[::-1]))

    candidates.discard(value)
    nearest = min(candidates, key=lambda candidate: (abs(candidate - value), candidate))
    return str(nearest)

class Solution:
    def nearestPalindromic(self, n: str) -> str:
        return solve(n)
