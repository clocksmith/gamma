# Original implementation. Contract: https://leetcode.com/problems/minimum-health-to-beat-game/
def solve(damage,armor):return sum(damage)-min(max(damage),armor)+1
