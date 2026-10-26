"""2870. Minimum Number of Operations to Make Array Empty: split each frequency into groups of two and three."""


def solve(nums: list[int]) -> int:
    """O(n) expected time and O(n) auxiliary space; inputs are read-only."""
    counts = {}
    for value in nums:
        counts[value] = counts.get(value, 0) + 1
    answer = 0
    for count in counts.values():
        if count == 1:
            return -1
        answer += (count + 2) // 3
    return answer


class Solution:
    def minOperations(self, nums: list[int]) -> int:
        return solve(nums)
