"""1755. Closest Subsequence Sum: meet-in-the-middle subset sums and binary search; O(n*2^(n/2)) time and O(2^(n/2)) space."""

from bisect import bisect_left


def solve(nums: list[int], goal: int) -> int:
    middle = len(nums) // 2

    def sums(values):
        result = [0]
        for value in values:
            result += [previous + value for previous in result]
        return result

    left = sums(nums[:middle])
    right = sorted(sums(nums[middle:]))
    answer = abs(goal)
    for value in left:
        desired = goal - value
        position = bisect_left(right, desired)
        if position < len(right):
            answer = min(answer, abs(desired - right[position]))
        if position > 0:
            answer = min(answer, abs(desired - right[position - 1]))
        if answer == 0:
            break
    return answer


class Solution:
    def minAbsDifference(self, nums: list[int], goal: int) -> int:
        return solve(nums, goal)
