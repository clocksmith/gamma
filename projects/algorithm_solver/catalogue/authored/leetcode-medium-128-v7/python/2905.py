"""2905. Find Indices With Index and Value Difference II: track eligible prefix minima and maxima while advancing the right endpoint."""


def solve(nums: list[int], indexDifference: int, valueDifference: int) -> list[int]:
    """O(n) time and O(1) auxiliary space; inputs are read-only."""
    smallest = largest = 0
    for right in range(indexDifference, len(nums)):
        entering = right - indexDifference
        if nums[entering] < nums[smallest]:
            smallest = entering
        if nums[entering] > nums[largest]:
            largest = entering
        if nums[right] - nums[smallest] >= valueDifference:
            return [smallest, right]
        if nums[largest] - nums[right] >= valueDifference:
            return [largest, right]
    return [-1, -1]


class Solution:
    def findIndices(self, nums: list[int], indexDifference: int, valueDifference: int) -> list[int]:
        return solve(nums, indexDifference, valueDifference)
