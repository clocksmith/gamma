"""3036. Number of Subarrays That Match a Pattern II.

KMP over adjacent comparison signs; O(n+m) time, O(m) space. Inputs are preserved.
"""

def solve(nums: list[int], pattern: list[int]) -> int:
    border = [0] * len(pattern)
    for index in range(1, len(pattern)):
        length = border[index - 1]
        while length and pattern[index] != pattern[length]:
            length = border[length - 1]
        border[index] = length + (pattern[index] == pattern[length])
    answer = length = 0
    for index in range(1, len(nums)):
        comparison = (nums[index] > nums[index - 1]) - (nums[index] < nums[index - 1])
        while length and comparison != pattern[length]:
            length = border[length - 1]
        if comparison == pattern[length]:
            length += 1
        if length == len(pattern):
            answer += 1
            length = border[length - 1]
    return answer


class Solution:
    def countMatchingSubarrays(self, nums: list[int], pattern: list[int]) -> int:
        return solve(nums, pattern)
