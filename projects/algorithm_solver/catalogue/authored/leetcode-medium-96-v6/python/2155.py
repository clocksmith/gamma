"""2155. All Divisions With the Highest Score of a Binary Array: move the division while maintaining left zeros and right ones."""


def solve(nums: list[int]) -> list[int]:
    """O(n) time and O(n) result space; inputs are read-only."""
    left_zeros = 0
    right_ones = sum(nums)
    best = -1
    result = []
    for index in range(len(nums) + 1):
        score = left_zeros + right_ones
        if score > best:
            best = score
            result = [index]
        elif score == best:
            result.append(index)
        if index < len(nums):
            if nums[index] == 0:
                left_zeros += 1
            else:
                right_ones -= 1
    return result


class Solution:
    def maxScoreIndices(self, nums: list[int]) -> list[int]:
        return solve(nums)
