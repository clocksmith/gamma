"""3845. Maximum Subarray XOR with Bounded Range."""
from __future__ import annotations
from collections import deque


def solve(nums: list[int], k: int) -> int:
    """O(n B + 2^B) time and O(n + 2^B) space, B=15; sliding extrema and a counted prefix-XOR trie."""
    base = 1 << 15
    counts = [0] * (2 * base)
    def change(value, delta):
        index = base + value
        while index:
            counts[index] += delta
            index //= 2

    def maximum_xor(value):
        node = 1
        answer = 0
        for bit in range(14, -1, -1):
            direction = (value >> bit) & 1
            opposite = node * 2 + (direction ^ 1)
            if counts[opposite]:
                answer |= 1 << bit
                node = opposite
            else:
                node = node * 2 + direction
        return answer

    minimum = deque()
    maximum = deque()
    prefix = [0]
    change(0, 1)
    left = 0
    answer = 0
    for right, value in enumerate(nums):
        prefix.append(prefix[-1] ^ value)
        while minimum and nums[minimum[-1]] >= value:
            minimum.pop()
        while maximum and nums[maximum[-1]] <= value:
            maximum.pop()
        minimum.append(right)
        maximum.append(right)
        while nums[maximum[0]] - nums[minimum[0]] > k:
            change(prefix[left], -1)
            if minimum[0] == left:
                minimum.popleft()
            if maximum[0] == left:
                maximum.popleft()
            left += 1
        answer = max(answer, maximum_xor(prefix[-1]))
        change(prefix[-1], 1)
    return answer


class Solution:
    def maxXor(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
