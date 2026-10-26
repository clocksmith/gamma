"""3849. Maximum Bitwise XOR After Rearrangement."""
from __future__ import annotations


def solve(s: str, t: str) -> str:
    """O(n) time and O(n) output space; greedily maximize each bit with remaining character counts."""
    counts = [t.count('0'), t.count('1')]
    result = []
    for char in s:
        bit = int(char)
        opposite = bit ^ 1
        if counts[opposite]:
            counts[opposite] -= 1
            result.append('1')
        else:
            counts[bit] -= 1
            result.append('0')
    return ''.join(result)


class Solution:
    def maximumXor(self, s: str, t: str) -> str:
        return solve(s, t)
