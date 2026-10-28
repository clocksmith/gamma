"""893. Groups of Special-Equivalent Strings (Medium).

Specification: https://leetcode.com/problems/groups-of-special-equivalent-strings/description/
"""


def solve(words: list[str]) -> int:
    groups = set()
    for word in words:
        even = "".join(sorted(word[i] for i in range(0, len(word), 2)))
        odd = "".join(sorted(word[i] for i in range(1, len(word), 2)))
        groups.add(even + '|' + odd)
    return len(groups)


class Solution:
    def numSpecialEquivGroups(self, words: list[str]) -> int:
        return solve(words)
