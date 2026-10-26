"""1300. Sum of Mutated Array Closest to Target: binary search the cap then compare its two neighboring sums."""


def solve(arr: list[int], target: int) -> int:
    """O(n log(M + 1)) time and O(1) auxiliary space, where M is the largest value; inputs are read-only."""
    low, high = 0, max(arr)
    while low < high:
        middle = (low + high) // 2
        total = sum(min(value, middle) for value in arr)
        if total < target:
            low = middle + 1
        else:
            high = middle
    if low == 0:
        return 0
    upper = sum(min(value, low) for value in arr)
    lower = sum(min(value, low - 1) for value in arr)
    return low - 1 if abs(lower - target) <= abs(upper - target) else low


class Solution:
    def findBestValue(self, arr: list[int], target: int) -> int:
        return solve(arr, target)
