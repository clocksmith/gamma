"""378. Kth Smallest Element in a Sorted Matrix."""
import heapq

def solve(matrix: list[list[int]], k: int) -> int:
    heap = [(matrix[row][0], row, 0) for row in range(min(k, len(matrix)))]
    heapq.heapify(heap)
    value = 0
    for _ in range(k):
        value, row, column = heapq.heappop(heap)
        if column + 1 < len(matrix[row]):
            heapq.heappush(heap, (matrix[row][column + 1], row, column + 1))
    return value

class Solution:
    def kthSmallest(self, matrix: list[list[int]], k: int) -> int:
        return solve(matrix, k)
