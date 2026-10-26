"""2963. Count the Number of Good Partitions: merge value-occurrence intervals and choose independent boundaries."""


def solve(nums: list[int]) -> int:
    """O(n) expected time and O(n) auxiliary space. Inputs are preserved."""
    last = {value: index for index, value in enumerate(nums)}
    end = 0
    answer = 1
    for index, value in enumerate(nums):
        end = max(end, last[value])
        if index == end and index + 1 < len(nums):
            answer = answer * 2 % 1_000_000_007
    return answer


class Solution:
    def numberOfGoodPartitions(self, nums: list[int]) -> int:
        return solve(nums)
