"""1202. Smallest String With Swaps (Medium).

Specification: https://leetcode.com/problems/smallest-string-with-swaps/description/
"""


def solve(s: str, pairs: list[list[int]]) -> str:
    n = len(s)
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, b in pairs:
        parent[find(a)] = find(b)
    groups = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(i)
    result = list(s)
    for indices in groups.values():
        indices = sorted(indices)
        chars = sorted(s[i] for i in indices)
        for index, ch in zip(indices, chars):
            result[index] = ch
    return "".join(result)


class Solution:
    def smallestStringWithSwaps(self, s: str, pairs: list[list[int]]) -> str:
        return solve(s, pairs)
