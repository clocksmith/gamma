"""3049. Earliest Second to Mark Indices II.

Binary search with reverse-time greedy selection of resets and reserved later marks; O(m log n log m) time, O(n+m) space. Inputs are preserved.
"""

from heapq import heappop, heappush


def solve(nums: list[int], changeIndices: list[int]) -> int:
    n, m = len(nums), len(changeIndices)
    first = [m] * n
    for second, value in enumerate(changeIndices):
        first[value - 1] = min(first[value - 1], second)
    baseline = sum(nums) + n

    def possible(limit):
        free = saved = 0
        selected = []
        for second in range(limit - 1, -1, -1):
            index = changeIndices[second] - 1
            if first[index] != second or nums[index] <= 1:
                free += 1
                continue
            heappush(selected, nums[index])
            saved += nums[index] + 1
            free -= 1
            if free < 0:
                saved -= heappop(selected) + 1
                free += 2
        return free >= baseline - saved

    if n > m or not possible(m):
        return -1
    low, high = n, m
    while low < high:
        middle = (low + high) // 2
        if possible(middle):
            high = middle
        else:
            low = middle + 1
    return low


class Solution:
    def earliestSecondToMarkIndices(self, nums: list[int], changeIndices: list[int]) -> int:
        return solve(nums, changeIndices)
