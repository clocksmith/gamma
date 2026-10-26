"""1764. Form Array by Concatenating Subarrays of Another Array: match each group at its earliest available position with a prefix-function search."""


def solve(groups: list[list[int]], nums: list[int]) -> bool:
    """O(n + g) time and O(m) auxiliary space, with g total group elements and m the largest group; inputs are read-only."""
    position = 0
    for group in groups:
        failure = [0] * len(group)
        matched = 0
        for index in range(1, len(group)):
            while matched and group[index] != group[matched]:
                matched = failure[matched - 1]
            if group[index] == group[matched]:
                matched += 1
            failure[index] = matched
        matched = 0
        while position < len(nums) and matched < len(group):
            value = nums[position]
            while matched and value != group[matched]:
                matched = failure[matched - 1]
            if value == group[matched]:
                matched += 1
            position += 1
        if matched != len(group):
            return False
    return True


class Solution:
    def canChoose(self, groups: list[list[int]], nums: list[int]) -> bool:
        return solve(groups, nums)
