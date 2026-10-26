"""2616. Minimize the Maximum Difference of Pairs: binary search the permitted gap and greedily pair adjacent sorted values."""


def solve(nums: list[int], p: int) -> int:
    """O(n log n + n log(M + 1)) time and O(n) auxiliary space, where M is the value range; inputs are read-only."""
    if p == 0:
        return 0
    ordered = sorted(nums)
    low, high = 0, ordered[-1] - ordered[0]
    while low < high:
        bound = (low + high) // 2
        pairs = 0
        index = 1
        while index < len(ordered):
            if ordered[index] - ordered[index - 1] <= bound:
                pairs += 1
                index += 2
            else:
                index += 1
        if pairs >= p:
            high = bound
        else:
            low = bound + 1
    return low


class Solution:
    def minimizeMax(self, nums: list[int], p: int) -> int:
        return solve(nums, p)
