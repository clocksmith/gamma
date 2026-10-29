"""Hack2Hire 67840e27d0faf7ec64cc3adb (Count Reversing Triples) over an INFERRED spec; qualification unknown."""


def solve(nums):
    values = sorted(set(nums))
    rank = {v: i + 1 for i, v in enumerate(values)}
    size = len(values)
    below = [0] * (size + 2)  # below[r]: number of elements with rank < r
    for v in nums:
        below[rank[v] + 1] += 1
    for r in range(1, size + 2):
        below[r] += below[r - 1]
    tree = [0] * (size + 1)
    equal = {}
    total = 0
    for j, v in enumerate(nums):
        r = rank[v]
        less_left = 0
        i = r - 1
        while i > 0:
            less_left += tree[i]
            i -= i & -i
        same_left = equal.get(r, 0)
        greater_left = j - less_left - same_left
        less_right = below[r] - less_left
        total += greater_left * less_right
        equal[r] = same_left + 1
        i = r
        while i <= size:
            tree[i] += 1
            i += i & -i
    return total


class Solution:
    def countTriplets(self, nums):
        return solve(nums)
