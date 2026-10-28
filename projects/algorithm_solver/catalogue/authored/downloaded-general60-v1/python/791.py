"""791. Custom Sort String (Medium).

Specification: https://leetcode.com/problems/custom-sort-string/description/
"""


def solve(order: str, s: str) -> str:
    rank = {ch: i for i, ch in enumerate(order)}
    ordered = []
    rest = []
    for ch in s:
        if ch in rank:
            ordered.append(ch)
        else:
            rest.append(ch)
    ordered.sort(key=lambda ch: rank[ch])
    return "".join(ordered) + "".join(rest)


class Solution:
    def customSortString(self, order: str, s: str) -> str:
        return solve(order, s)
