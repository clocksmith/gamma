"""1713. Minimum Operations to Make a Subsequence."""

from bisect import bisect_left


def solve(target: list[int], arr: list[int]) -> int:
    """O(n + m*log(n+1)) time, O(n) space; target values are distinct."""
    positions = {value: index for index, value in enumerate(target)}
    tails = []
    for value in arr:
        if value not in positions:
            continue
        position = positions[value]
        slot = bisect_left(tails, position)
        if slot == len(tails):
            tails.append(position)
        else:
            tails[slot] = position
    return len(target) - len(tails)


class Solution:
    def minOperations(self, target: list[int], arr: list[int]) -> int:
        return solve(target, arr)
