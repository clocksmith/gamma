"""Original frontend 3825 variant; qualification unknown."""

def solve(nums):
    from bisect import bisect_left
    answer = 0
    for bit in range(29):
        tails = []
        for value in nums:
            if value & (1 << bit):
                index = bisect_left(tails, value)
                if index == len(tails):
                    tails.append(value)
                else:
                    tails[index] = value
        answer = max(answer, len(tails))
    return answer


class Solution:
    def longestSubsequence(self, nums):
        return solve(nums)
