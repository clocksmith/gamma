"""Original candidate for LeetCode 3186. Contract: https://leetcode.com/problems/maximum-total-damage-with-spell-casting/
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O(n log n) time, O(n) space; sum <= 10^14, exact in JS Number"""
from collections import Counter

def solve(power):
    counts=Counter(power);values=sorted(counts);dp=[0];j=0
    for i,x in enumerate(values):
        while j<i and values[j]<x-2:j+=1
        dp.append(max(dp[-1],dp[j]+x*counts[x]))
    return dp[-1]
