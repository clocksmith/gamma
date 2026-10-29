"""Original LeetCode 632 candidate; qualification unknown."""

import heapq

def solve(nums):
    heap = [(row[0], i, 0) for i, row in enumerate(nums)]
    heapq.heapify(heap)
    high = max(row[0] for row in nums)
    best = [heap[0][0], high]
    while True:
        low, row, column = heapq.heappop(heap)
        if (high - low, low) < (best[1] - best[0], best[0]):
            best = [low, high]
        column += 1
        if column == len(nums[row]):
            return best
        value = nums[row][column]
        high = max(high, value)
        heapq.heappush(heap, (value, row, column))


class Solution:
    def smallestRange(self, nums):
        return solve(nums)
