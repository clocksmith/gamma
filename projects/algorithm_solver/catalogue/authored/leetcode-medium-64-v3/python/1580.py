"""1580. Put Boxes Into the Warehouse II: match boxes to capacities reachable from either entrance."""


def solve(boxes: list[int], warehouse: list[int]) -> int:
    """O(b log b + w log w) time and O(b + w) auxiliary space; inputs are read-only."""
    ordered = sorted(boxes)
    capacities = []
    bottleneck = float('inf')
    for height in warehouse:
        bottleneck = min(bottleneck, height)
        capacities.append(bottleneck)
    bottleneck = float('inf')
    for index in range(len(warehouse) - 1, -1, -1):
        bottleneck = min(bottleneck, warehouse[index])
        capacities[index] = max(capacities[index], bottleneck)
    capacities.sort()
    placed = 0
    for capacity in capacities:
        if placed < len(ordered) and ordered[placed] <= capacity:
            placed += 1
    return placed


class Solution:
    def maxBoxesInWarehouse(self, boxes: list[int], warehouse: list[int]) -> int:
        return solve(boxes, warehouse)
