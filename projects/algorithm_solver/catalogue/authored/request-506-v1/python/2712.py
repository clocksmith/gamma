# Original implementation. Contract: https://leetcode.com/problems/minimum-cost-to-make-all-characters-equal/
def solve(s):
    return sum(min(i,len(s)-i) for i in range(1,len(s)) if s[i]!=s[i-1])
