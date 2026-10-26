"""1681. Minimum Incompatibility: valid-group masks with first-unused-index symmetry breaking; O(3^n+n*2^n) time and O(2^n) space."""

from collections import Counter


def solve(nums: list[int], k: int) -> int:
    size = len(nums)
    group_size = size // k
    if max(Counter(nums).values()) > k:
        return -1
    limit = 1 << size
    groups = [[] for _ in range(size)]
    for mask in range(1, limit):
        if mask.bit_count() != group_size:
            continue
        values = {nums[index] for index in range(size) if mask & (1 << index)}
        if len(values) != group_size:
            continue
        first = (mask & -mask).bit_length() - 1
        groups[first].append((mask, max(values) - min(values)))
    best = [float('inf')] * limit
    best[0] = 0
    full = limit - 1
    for used in range(full):
        if best[used] == float('inf'):
            continue
        available = full ^ used
        first = (available & -available).bit_length() - 1
        for mask, price in groups[first]:
            if mask & used == 0:
                following = mask | used
                best[following] = min(best[following], best[used] + price)
    return -1 if best[full] == float('inf') else best[full]


class Solution:
    def minimumIncompatibility(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
