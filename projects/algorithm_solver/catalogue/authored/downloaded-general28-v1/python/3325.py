"""3325. Count Substrings With K-Frequency Characters I (Medium).

Specification: https://leetcode.com/problems/count-substrings-with-k-frequency-characters-i/description/
"""


def solve(s: str, k: int) -> int:
    count = {}
    left = 0
    ans = 0
    for right, ch in enumerate(s):
        count[ch] = count.get(ch, 0) + 1
        while count.get(ch, 0) >= k:
            lc = s[left]
            count[lc] = count.get(lc, 0) - 1
            left += 1
        ans += left
    return ans


class Solution:
    def numberOfSubstrings(self, s: str, k: int) -> int:
        return solve(s, k)
