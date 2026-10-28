"""458. Poor Pigs (Hard).

Specification: https://leetcode.com/problems/poor-pigs/description/
"""


def solve(buckets: int, minutesToDie: int, minutesToTest: int) -> int:
    states = minutesToTest // minutesToDie + 1
    pigs = 0
    capacity = 1
    while capacity < buckets:
        capacity *= states
        pigs += 1
    return pigs


class Solution:
    def poorPigs(self, buckets: int, minutesToDie: int, minutesToTest: int) -> int:
        return solve(buckets, minutesToDie, minutesToTest)
