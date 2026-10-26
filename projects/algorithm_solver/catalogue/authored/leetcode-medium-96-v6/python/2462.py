"""2462. Total Cost to Hire K Workers: merge the two candidate frontiers in a cost-then-index heap and refill the chosen side."""
from heapq import heapify, heappop, heappush


def solve(costs: list[int], k: int, candidates: int) -> int:
    """O((c + k) log(c + 1)) time and O(c) auxiliary space for c = min(n, 2 * candidates); inputs are read-only."""
    heap = []
    left, right = 0, len(costs) - 1
    for _ in range(candidates):
        if left > right:
            break
        heap.append((costs[left], left, 0))
        left += 1
    for _ in range(candidates):
        if left > right:
            break
        heap.append((costs[right], right, 1))
        right -= 1
    heapify(heap)
    total = 0
    for _ in range(k):
        cost, _, side = heappop(heap)
        total += cost
        if left <= right:
            if side == 0:
                heappush(heap, (costs[left], left, side))
                left += 1
            else:
                heappush(heap, (costs[right], right, side))
                right -= 1
    return total


class Solution:
    def totalCost(self, costs: list[int], k: int, candidates: int) -> int:
        return solve(costs, k, candidates)
