"""1248. Count Number of Nice Subarrays: count matching odd-prefix totals."""


def solve(nums: list[int], k: int) -> int:
    """O(n) time and O(n) auxiliary space; inputs are read-only."""
    frequencies = [0] * (len(nums) + 1)
    frequencies[0] = 1
    odd_count = answer = 0
    for value in nums:
        odd_count += value % 2
        if odd_count >= k:
            answer += frequencies[odd_count - k]
        frequencies[odd_count] += 1
    return answer


class Solution:
    def numberOfSubarrays(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
