"""2593. Find Score of an Array After Marking All Elements: visit indices in value-and-index order and mark neighboring positions."""


def solve(nums: list[int]) -> int:
    """O(n log n) time and O(n) auxiliary space; inputs are read-only."""
    order = sorted(range(len(nums)), key=lambda index: (nums[index], index))
    marked = [False] * len(nums)
    score = 0
    for index in order:
        if marked[index]:
            continue
        score += nums[index]
        for neighbor in range(max(0, index - 1), min(len(nums), index + 2)):
            marked[neighbor] = True
    return score


class Solution:
    def findScore(self, nums: list[int]) -> int:
        return solve(nums)
