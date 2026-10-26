"""2916. Subarrays Distinct Element Sum of Squares II. Maintain distinct-count range increments with two Fenwick trees."""


def solve(nums: list[int]) -> int:
    """O(n log n) time and O(n) space. Inputs are preserved."""
    modulus = 1_000_000_007
    size = len(nums)
    slope = [0] * (size + 2)
    offset = [0] * (size + 2)

    def add(tree, index, delta):
        while index <= size + 1:
            tree[index] += delta
            index += index & -index

    def prefix(tree, index):
        total = 0
        while index > 0:
            total += tree[index]
            index -= index & -index
        return total

    def sum_through(index):
        return prefix(slope, index) * index - prefix(offset, index)

    previous = {}
    ending = 0
    answer = 0
    for index, value in enumerate(nums):
        left = previous.get(value, -1) + 2
        right = index + 1
        old_sum = sum_through(right) - sum_through(left - 1)
        ending = (ending + 2 * old_sum + right - left + 1) % modulus
        answer = (answer + ending) % modulus
        add(slope, left, 1)
        add(slope, right + 1, -1)
        add(offset, left, left - 1)
        add(offset, right + 1, -right)
        previous[value] = index
    return answer


class Solution:
    def sumCounts(self, nums: list[int]) -> int:
        return solve(nums)
