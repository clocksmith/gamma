# Original candidate implementation. Contract: https://leetcode.com/problems/find-maximal-uncovered-ranges/
def solve(n,ranges):
    out=[];next_free=0
    for left,right in sorted(ranges):
        if left>next_free:out.append([next_free,left-1])
        next_free=max(next_free,right+1)
    if next_free<n:out.append([next_free,n-1])
    return out
