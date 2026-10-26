"""3811. Number of Alternating XOR Partitions."""
from __future__ import annotations


def solve(nums: list[int], target1: int, target2: int) -> int:
    """O(n) expected time and O(n) space; snapshots both transitions before adding the current prefix."""
    modulus = 1_000_000_007
    even = {0: 1}
    odd = {}
    prefix = 0
    last_even = last_odd = 0
    for value in nums:
        prefix ^= value
        last_odd = even.get(prefix ^ target1, 0)
        last_even = odd.get(prefix ^ target2, 0)
        odd[prefix] = (odd.get(prefix, 0) + last_odd) % modulus
        even[prefix] = (even.get(prefix, 0) + last_even) % modulus
    return (last_even + last_odd) % modulus


class Solution:
    def countPartitions(self, nums: list[int], target1: int, target2: int) -> int:
        return solve(nums, target1, target2)
