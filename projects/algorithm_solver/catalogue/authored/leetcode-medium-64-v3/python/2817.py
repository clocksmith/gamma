"""2817. Minimum Absolute Difference Between Elements With Constraint: query predecessor and successor among sufficiently old values with a Fenwick tree."""


def solve(nums: list[int], x: int) -> int:
    """O(n log n) time and O(n) auxiliary space; inputs are read-only."""
    if x == 0:
        return 0
    values = sorted(set(nums))
    ranks = {value: index + 1 for index, value in enumerate(values)}
    tree = [0] * (len(values) + 1)

    def insert(index):
        while index < len(tree):
            tree[index] += 1
            index += index & -index

    def prefix_count(index):
        total = 0
        while index:
            total += tree[index]
            index -= index & -index
        return total

    def select(order):
        index = 0
        step = 1 << (len(values).bit_length() - 1)
        while step:
            following = index + step
            if following < len(tree) and tree[following] < order:
                order -= tree[following]
                index = following
            step //= 2
        return values[index]

    best = float('inf')
    for index in range(x, len(nums)):
        insert(ranks[nums[index - x]])
        value = nums[index]
        below = prefix_count(ranks[value] - 1)
        if below:
            best = min(best, value - select(below))
        if below < index - x + 1:
            best = min(best, select(below + 1) - value)
    return best


class Solution:
    def minAbsoluteDifference(self, nums: list[int], x: int) -> int:
        return solve(nums, x)
