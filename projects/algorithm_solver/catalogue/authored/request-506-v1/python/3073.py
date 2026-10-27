# Original implementation. Contract: https://leetcode.com/problems/maximum-increasing-triplet-value/
from bisect import bisect_left
def solve(nums):
    n=len(nums);ordered=sorted(set(nums));bit=[0]*(len(ordered)+1);suffix=[0]*(n+1)
    for i in range(n-1,-1,-1):suffix[i]=max(suffix[i+1],nums[i])
    answer=0
    for j,x in enumerate(nums):
        rank=bisect_left(ordered,x);i=rank;left=0
        while i:left=max(left,bit[i]);i-=i&-i
        if left and suffix[j+1]>x:answer=max(answer,left-x+suffix[j+1])
        i=rank+1
        while i<len(bit):bit[i]=max(bit[i],x);i+=i&-i
    return answer
