"""839. Similar String Groups (Hard).

Specification: https://leetcode.com/problems/similar-string-groups/description/
"""


def solve(strs: list[str]) -> int:
    n = len(strs)
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    def similar(a, b):
        diff = 0
        for i in range(len(a)):
            if a[i] != b[i]:
                diff += 1
                if diff > 2:
                    return False
        return True

    for i in range(n):
        for j in range(i + 1, n):
            if similar(strs[i], strs[j]):
                union(i, j)
    return len({find(i) for i in range(n)})


class Solution:
    def numSimilarGroups(self, strs: list[str]) -> int:
        return solve(strs)
