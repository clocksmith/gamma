"""1090. Largest Values From Labels (Medium).

Specification: https://leetcode.com/problems/largest-values-from-labels/description/
"""


def solve(values: list[int], labels: list[int], numWanted: int, useLimit: int) -> int:
    items = sorted(zip(values, labels), key=lambda item: -item[0])
    counts = {}
    total = 0
    taken = 0
    for value, label in items:
        if taken >= numWanted:
            break
        used = counts.get(label, 0)
        if used < useLimit:
            total += value
            counts[label] = used + 1
            taken += 1
    return total


class Solution:
    def largestValsFromLabels(self, values: list[int], labels: list[int], numWanted: int, useLimit: int) -> int:
        return solve(values, labels, numWanted, useLimit)
