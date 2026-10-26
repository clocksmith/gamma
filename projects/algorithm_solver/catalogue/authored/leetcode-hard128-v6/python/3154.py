"""3154. Find Number of Ways to Reach the K-th Stair.

For j forward jumps choose the nonadjacent downward moves among j+1 gaps; O(log^2(k+2)) time and O(1) space.
"""

from math import comb


def solve(k: int) -> int:
    answer = jumps = 0
    power = 1
    while power - jumps - 1 <= k:
        backwards = power - k
        if 0 <= backwards <= jumps + 1:
            answer += comb(jumps + 1, backwards)
        jumps += 1
        power *= 2
    return answer


class Solution:
    def waysToReachStair(self, k: int) -> int:
        return solve(k)
