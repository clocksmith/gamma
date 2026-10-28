"""1234. Replace the Substring for Balanced String (Medium).

Specification: https://leetcode.com/problems/replace-the-substring-for-balanced-string/description/
"""


def solve(s: str) -> int:
    n = len(s)
    target = n // 4
    counts = {'Q': 0, 'W': 0, 'E': 0, 'R': 0}
    for ch in s:
        counts[ch] += 1
    if all(counts[ch] == target for ch in 'QWER'):
        return 0
    best = n
    left = 0
    window = {'Q': 0, 'W': 0, 'E': 0, 'R': 0}

    def outside_ok():
        return all(counts[ch] - window[ch] <= target for ch in 'QWER')

    for right, ch in enumerate(s):
        window[ch] += 1
        while left <= right and outside_ok():
            best = min(best, right - left + 1)
            window[s[left]] -= 1
            left += 1
    return best


class Solution:
    def balancedString(self, s: str) -> int:
        return solve(s)
