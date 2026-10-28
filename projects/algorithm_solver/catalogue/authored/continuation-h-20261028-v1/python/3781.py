"""Original frontend 3781 development variant; qualification unknown."""

def solve(nums, s):
    import heapq
    available = []
    answer = 0
    for value, bit in zip(nums, s):
        heapq.heappush(available, -value)
        if bit == '1':
            answer -= heapq.heappop(available)
    return answer


class Solution:
    def maximumScore(self, nums, s):
        return solve(nums, s)
