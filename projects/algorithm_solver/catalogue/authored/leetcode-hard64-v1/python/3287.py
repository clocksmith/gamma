"""3287. Find the Maximum Sequence Value of Array: combine exact-count OR states on both sides of every split."""


def solve(nums: list[int], k: int) -> int:
    """O(n*k*U + n*U^2) time and O((n+k)*U) space, U=128. Inputs are preserved."""
    n = len(nums)
    left_states = [None] * n
    states = [set() for _ in range(k + 1)]
    states[0].add(0)
    for index, value in enumerate(nums):
        for chosen in range(min(k, index + 1), 0, -1):
            states[chosen].update(previous | value for previous in states[chosen - 1])
        left_states[index] = states[k].copy()
    states = [set() for _ in range(k + 1)]
    states[0].add(0)
    answer = 0
    for index in range(n - 1, -1, -1):
        for chosen in range(min(k, n - index), 0, -1):
            states[chosen].update(previous | nums[index] for previous in states[chosen - 1])
        if index >= k and n - index >= k:
            for left in left_states[index - 1]:
                for right in states[k]:
                    answer = max(answer, left ^ right)
    return answer


class Solution:
    def maxValue(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
