from bisect import bisect_left, bisect_right

def solve(robots, distance, walls):
    ordered = sorted(zip(robots, distance))
    positions = sorted(walls)
    def count(lo, hi):
        return max(0, bisect_right(positions, hi)-bisect_left(positions, lo)) if lo <= hi else 0
    fixed = sum(count(p, p) for p, d in ordered)
    first, reach = ordered[0]
    dp = [count(first-reach, first-1), 0]
    for i in range(1, len(ordered)):
        a, da = ordered[i-1]
        b, db = ordered[i]
        right_end = min(b-1, a+da)
        left_start = max(a+1, b-db)
        r = count(a+1, right_end)
        l = count(left_start, b-1)
        overlap = count(left_start, right_end)
        dp = [max(dp[0]+l, dp[1]+r+l-overlap), max(dp[0], dp[1]+r)]
    last, reach = ordered[-1]
    return fixed+max(dp[0], dp[1]+count(last+1,last+reach))

class Solution:
    def maxWalls(self, robots, distance, walls):
        return solve(robots, distance, walls)
