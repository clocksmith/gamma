"""2552. Count Increasing Quadruplets. Maintain the number of valid three-index prefixes for each high middle index."""


def solve(nums: list[int]) -> int:
    """O(n^2) time and O(n) space. Inputs are preserved."""
    triples = [0] * len(nums)
    answer = 0
    for last, value in enumerate(nums):
        smaller = 0
        for middle in range(last):
            if nums[middle] < value:
                answer += triples[middle]
                smaller += 1
            elif nums[middle] > value:
                triples[middle] += smaller
    return answer


class Solution:
    def countQuadruplets(self, nums: list[int]) -> int:
        return solve(nums)
