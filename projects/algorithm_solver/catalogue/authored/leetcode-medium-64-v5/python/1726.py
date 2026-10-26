"""1726. Tuple with Same Product: count earlier unordered pairs with the same product."""


def solve(nums: list[int]) -> int:
    """O(n^2) expected time and O(n^2) auxiliary space; inputs are read-only."""
    counts = {}
    result = 0
    for right in range(len(nums)):
        for left in range(right):
            product = nums[left] * nums[right]
            previous = counts.get(product, 0)
            result += 8 * previous
            counts[product] = previous + 1
    return result


class Solution:
    def tupleSameProduct(self, nums: list[int]) -> int:
        return solve(nums)
