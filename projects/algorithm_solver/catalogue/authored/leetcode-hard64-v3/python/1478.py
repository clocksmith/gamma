"""1478. Allocate Mailboxes: median interval costs and partition DP; O(k*n^2) time and O(n^2) space."""


def solve(houses: list[int], k: int) -> int:
    positions = sorted(houses)
    size = len(positions)
    if k >= size:
        return 0
    cost = [[0] * size for _ in range(size)]
    for width in range(2, size + 1):
        for left in range(size - width + 1):
            right = left + width - 1
            cost[left][right] = positions[right] - positions[left]
            if width > 2:
                cost[left][right] += cost[left + 1][right - 1]
    previous = [0] + [float('inf')] * size
    for groups in range(1, k + 1):
        current = [float('inf')] * (size + 1)
        for covered in range(groups, size + 1):
            for split in range(groups - 1, covered):
                current[covered] = min(current[covered], previous[split] + cost[split][covered - 1])
        previous = current
    return previous[size]


class Solution:
    def minDistance(self, houses: list[int], k: int) -> int:
        return solve(houses, k)
