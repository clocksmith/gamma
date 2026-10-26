"""1675. Minimize Deviation in Array: normalize odd values, then reduce the maximum; O(n*log(n+1)*log(M+1)) time and O(n) space."""

from heapq import heapify, heappop, heappush


def solve(nums: list[int]) -> int:
    values = [value * 2 if value % 2 else value for value in nums]
    minimum = min(values)
    heap = [-value for value in values]
    heapify(heap)
    answer = float('inf')
    while heap:
        maximum = -heappop(heap)
        answer = min(answer, maximum - minimum)
        if maximum % 2:
            break
        maximum //= 2
        minimum = min(minimum, maximum)
        heappush(heap, -maximum)
    return answer


class Solution:
    def minimumDeviation(self, nums: list[int]) -> int:
        return solve(nums)
