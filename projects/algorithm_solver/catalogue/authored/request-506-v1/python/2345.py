# Original implementation. Contract: https://leetcode.com/problems/finding-the-number-of-visible-mountains/
from collections import Counter
def solve(peaks):
    counts=Counter((x-y,x+y) for x,y in peaks);end=-10**30;out=0
    for (l,r),count in sorted(counts.items(),key=lambda p:(p[0][0],-p[0][1])):
        if r>end:out+=count==1;end=r
    return out
