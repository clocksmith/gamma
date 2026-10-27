"""458. Poor Pigs. Each pig distinguishes completed-rounds plus survival outcomes; avoid logarithm rounding."""

def solve(buckets: int, minutesToDie: int, minutesToTest: int) -> int:
    if buckets <= 1:
        return 0
    states = minutesToTest // minutesToDie + 1
    if states <= 1:
        raise ValueError('No finite number of pigs distinguishes multiple buckets without a completed test round.')
    pigs, capacity = 0, 1
    while capacity < buckets:
        pigs += 1
        capacity *= states
    return pigs


class Solution:
    def poorPigs(self, buckets: int, minutesToDie: int, minutesToTest: int) -> int:
        return solve(buckets, minutesToDie, minutesToTest)
