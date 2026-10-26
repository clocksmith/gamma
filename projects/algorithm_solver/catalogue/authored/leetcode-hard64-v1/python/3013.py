"""3013. Divide an Array Into Subarrays With Minimum Cost II: sliding order statistics with count and sum Fenwick trees."""

from bisect import bisect_left


def solve(nums: list[int], k: int, dist: int) -> int:
    """O(n log n) time and O(n) auxiliary space. Inputs are preserved."""
    coordinates = sorted(set(nums[1:]))
    size = len(coordinates)
    counts = [0] * (size + 1)
    sums = [0] * (size + 1)

    def update(value, change):
        index = bisect_left(coordinates, value) + 1
        while index <= size:
            counts[index] += change
            sums[index] += change * value
            index += index & -index

    def smallest_sum(amount):
        index = 0
        total = 0
        step = 1 << (size.bit_length() - 1)
        while step:
            following = index + step
            if following <= size and counts[following] < amount:
                amount -= counts[following]
                total += sums[following]
                index = following
            step //= 2
        return total + amount * coordinates[index]

    for index in range(1, dist + 2):
        update(nums[index], 1)
    best = smallest_sum(k - 1)
    for right in range(dist + 2, len(nums)):
        update(nums[right - dist - 1], -1)
        update(nums[right], 1)
        best = min(best, smallest_sum(k - 1))
    return nums[0] + best


class Solution:
    def minimumCost(self, nums: list[int], k: int, dist: int) -> int:
        return solve(nums, k, dist)
