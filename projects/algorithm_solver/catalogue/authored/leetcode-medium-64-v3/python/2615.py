"""2615. Sum of Distances: accumulate equal-value index distances in forward and backward passes."""


def solve(nums: list[int]) -> list[int]:
    """O(n) expected time and O(n) auxiliary space; inputs are read-only."""
    answer = [0] * len(nums)
    counts = {}
    totals = {}
    for index, value in enumerate(nums):
        count = counts.get(value, 0)
        total = totals.get(value, 0)
        answer[index] += index * count - total
        counts[value] = count + 1
        totals[value] = total + index
    counts.clear()
    totals.clear()
    for index in range(len(nums) - 1, -1, -1):
        value = nums[index]
        count = counts.get(value, 0)
        total = totals.get(value, 0)
        answer[index] += total - index * count
        counts[value] = count + 1
        totals[value] = total + index
    return answer


class Solution:
    def distance(self, nums: list[int]) -> list[int]:
        return solve(nums)
