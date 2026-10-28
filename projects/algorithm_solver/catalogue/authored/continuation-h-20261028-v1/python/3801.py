"""Original frontend 3801 development variant; qualification unknown."""

def solve(lists):
    n = len(lists)
    size = 1 << n
    lengths = [0] * size
    medians = [0] * size
    tagged = sorted((value, 1 << i) for i, row in enumerate(lists) for value in row)
    for mask in range(1, size):
        bit = mask & -mask
        lengths[mask] = lengths[mask ^ bit] + len(lists[bit.bit_length() - 1])
        target = (lengths[mask] - 1) // 2
        seen = 0
        for value, origin in tagged:
            if mask & origin:
                if seen == target:
                    medians[mask] = value
                    break
                seen += 1
    dp = [0] * size
    for mask in range(1, size):
        if mask & (mask - 1) == 0:
            continue
        anchor = mask & -mask
        best = float('inf')
        subset = (mask - 1) & mask
        while subset:
            if subset & anchor:
                other = mask ^ subset
                best = min(best, dp[subset] + dp[other] + lengths[mask] + abs(medians[subset] - medians[other]))
            subset = (subset - 1) & mask
        dp[mask] = best
    return dp[-1]


class Solution:
    def minMergeCost(self, lists):
        return solve(lists)
