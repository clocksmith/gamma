"""1564. Put Boxes Into the Warehouse I: fill deepest usable rooms with the smallest remaining boxes."""


def solve(boxes: list[int], warehouse: list[int]) -> int:
    """O(b log b + w) time and O(b + w) space for b boxes and w rooms; inputs are read-only."""
    ordered = sorted(boxes)
    capacities = []
    bottleneck = float('inf')
    for height in warehouse:
        bottleneck = min(bottleneck, height)
        capacities.append(bottleneck)
    placed = 0
    for capacity in reversed(capacities):
        if placed < len(ordered) and ordered[placed] <= capacity:
            placed += 1
    return placed


class Solution:
    def maxBoxesInWarehouse(self, boxes: list[int], warehouse: list[int]) -> int:
        return solve(boxes, warehouse)
