"""1343. Number of Sub-arrays of Size K and Average Greater than or Equal to Threshold: compare sliding-window sums without floating-point averages."""


def solve(arr: list[int], k: int, threshold: int) -> int:
    """O(n) time and O(1) auxiliary space; inputs are read-only."""
    total = count = 0
    required = k * threshold
    for index, value in enumerate(arr):
        total += value
        if index >= k:
            total -= arr[index - k]
        if index + 1 >= k and total >= required:
            count += 1
    return count


class Solution:
    def numOfSubarrays(self, arr: list[int], k: int, threshold: int) -> int:
        return solve(arr, k, threshold)
