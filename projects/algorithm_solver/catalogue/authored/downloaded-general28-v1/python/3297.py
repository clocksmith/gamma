"""3297. Count Substrings That Can Be Rearranged to Contain a String I (Medium).

Specification: https://leetcode.com/problems/count-substrings-that-can-be-rearranged-to-contain-a-string-i/description/
"""


def solve(word1: str, word2: str) -> int:
    need = {}
    for ch in word2:
        need[ch] = need.get(ch, 0) + 1
    have = {}
    left = 0
    ans = 0
    for right, ch in enumerate(word1):
        have[ch] = have.get(ch, 0) + 1
        while left <= right:
            c = word1[left]
            if c not in need or have.get(c, 0) - 1 >= need[c]:
                have[c] = have.get(c, 0) - 1
                left += 1
            else:
                break
        if all(have.get(c, 0) >= k for c, k in need.items()):
            ans += left + 1
    return ans


class Solution:
    def validSubstringCount(self, word1: str, word2: str) -> int:
        return solve(word1, word2)
