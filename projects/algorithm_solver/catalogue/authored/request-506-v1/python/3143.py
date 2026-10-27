# Original candidate. Contract: https://leetcode.com/problems/maximum-points-inside-the-square/
def solve(points, s):
    nearest={};limit=float('inf')
    for (x,y),tag in zip(points,s):
        distance=max(abs(x),abs(y))
        if tag in nearest:limit=min(limit,max(distance,nearest[tag]));nearest[tag]=min(distance,nearest[tag])
        else:nearest[tag]=distance
    return sum(d<limit for d in nearest.values())
