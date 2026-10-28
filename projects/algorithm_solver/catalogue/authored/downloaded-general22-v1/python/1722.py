"""1722. Minimize Hamming Distance After Swap Operations (Medium).

Specification: https://leetcode.com/problems/minimize-hamming-distance-after-swap-operations/description/
"""


def solve(source: list[int], target: list[int], allowedSwaps: list[list[int]]) -> int:
    n = len(source)
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, b in allowedSwaps:
        parent[find(a)] = find(b)
    groups = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(i)
    answer = 0
    for indices in groups.values():
        counts = {}
        for i in indices:
            counts[source[i]] = counts.get(source[i], 0) + 1
        for i in indices:
            value = target[i]
            if counts.get(value, 0) > 0:
                counts[value] -= 1
            else:
                answer += 1
    return answer


class Solution:
    def minimumHammingDistance(self, source: list[int], target: list[int], allowedSwaps: list[list[int]]) -> int:
        return solve(source, target, allowedSwaps)
