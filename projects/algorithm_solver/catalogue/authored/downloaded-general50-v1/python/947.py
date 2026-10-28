"""947. Most Stones Removed with Same Row or Column (Medium).

Specification: https://leetcode.com/problems/most-stones-removed-with-same-row-or-column/description/
"""


def solve(stones: list[list[int]]) -> int:
    parent = list(range(len(stones)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        parent[find(a)] = find(b)

    for i in range(len(stones)):
        for j in range(i + 1, len(stones)):
            if stones[i][0] == stones[j][0] or stones[i][1] == stones[j][1]:
                union(i, j)
    components = {find(i) for i in range(len(stones))}
    return len(stones) - len(components)


class Solution:
    def removeStones(self, stones: list[list[int]]) -> int:
        return solve(stones)
