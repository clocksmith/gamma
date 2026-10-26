"""2763. Sum of Imbalance Numbers of All Subarrays: incremental connected components among distinct integers."""


def solve(nums: list[int]) -> int:
    """O(n^2) expected time and O(n) auxiliary space. Inputs are preserved."""
    answer = 0
    for left in range(len(nums)):
        seen = set()
        imbalance = -1
        for right in range(left, len(nums)):
            value = nums[right]
            if value not in seen:
                imbalance += 1 - int(value - 1 in seen) - int(value + 1 in seen)
                seen.add(value)
            answer += imbalance
    return answer


class Solution:
    def sumImbalanceNumbers(self, nums: list[int]) -> int:
        return solve(nums)
