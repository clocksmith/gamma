"""3330. Find the Original Typed String I (Easy).

Specification: https://leetcode.com/problems/find-the-original-typed-string-i/description/
"""


def solve(word: str) -> int:
    ans = 1
    for i in range(1, len(word)):
        if word[i] == word[i - 1]:
            ans += 1
    return ans


class Solution:
    def possibleStringCount(self, word: str) -> int:
        return solve(word)
