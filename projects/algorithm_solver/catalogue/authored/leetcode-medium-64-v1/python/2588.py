"""2588. Count the Number of Beautiful Subarrays: count equal prefix XORs so every bit occurs an even number of times."""


def solve(nums: list[int]) -> int:
    """O(n) expected time and O(n) auxiliary space; inputs are read-only."""
    counts = {0: 1}
    prefix = answer = 0
    for value in nums:
        prefix ^= value
        previous = counts.get(prefix, 0)
        answer += previous
        counts[prefix] = previous + 1
    return answer


class Solution:
    def beautifulSubarrays(self, nums: list[int]) -> int:
        return solve(nums)
