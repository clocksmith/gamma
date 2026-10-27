# Original implementation. Contract: https://leetcode.com/problems/longest-unequal-adjacent-groups-subsequence-i/
def solve(words,groups):
    out=[];last=-1
    for w,g in zip(words,groups):
        if g!=last:out.append(w);last=g
    return out
