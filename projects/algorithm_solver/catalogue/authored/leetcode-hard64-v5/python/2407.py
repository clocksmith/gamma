"""2407. Longest Increasing Subsequence II. Range-maximum segment tree over preceding values."""


def solve(nums: list[int], k: int) -> int:
    """O(M+n log M) time and O(M) space, M=max(nums)+1. Inputs are preserved."""
    size = 1
    while size <= max(nums):
        size *= 2
    tree = [0] * (2 * size)
    answer = 0
    for value in nums:
        left = size + max(0, value - k)
        right = size + value
        previous = 0
        while left < right:
            if left & 1:
                previous = max(previous, tree[left])
                left += 1
            if right & 1:
                right -= 1
                previous = max(previous, tree[right])
            left //= 2
            right //= 2
        current = previous + 1
        node = size + value
        tree[node] = max(tree[node], current)
        node //= 2
        while node:
            tree[node] = max(tree[2 * node], tree[2 * node + 1])
            node //= 2
        answer = max(answer, current)
    return answer


class Solution:
    def lengthOfLIS(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
