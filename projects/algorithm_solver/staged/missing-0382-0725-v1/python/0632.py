"""632. Smallest Range Covering Elements from K Lists."""

from heapq import heappush, heappop

def solve(nums: list[list[int]]) -> list[int]:
    heap = []
    maximum = float('-inf')
    for row, values in enumerate(nums):
        heappush(heap, (values[0], row, 0))
        maximum = max(maximum, values[0])
    answer = [heap[0][0], maximum]
    while heap:
        minimum, row, index = heappop(heap)
        if (maximum - minimum, minimum) < (answer[1] - answer[0], answer[0]):
            answer = [minimum, maximum]
        index += 1
        if index == len(nums[row]):
            break
        value = nums[row][index]
        maximum = max(maximum, value)
        heappush(heap, (value, row, index))
    return answer


class Solution:
    def smallestRange(self, nums: list[list[int]]) -> list[int]:
        return solve(nums)
