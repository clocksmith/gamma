"""646. Maximum Length of Pair Chain (Medium).

Specification: https://leetcode.com/problems/maximum-length-of-pair-chain/description/
"""


def solve(pairs: list[list[int]]) -> int:
    ordered = sorted(pairs, key=lambda pair: pair[1])
    count = 0
    current_end = float('-inf')
    for start, end in ordered:
        if start > current_end:
            count += 1
            current_end = end
    return count


class Solution:
    def findLongestChain(self, pairs: list[list[int]]) -> int:
        return solve(pairs)
