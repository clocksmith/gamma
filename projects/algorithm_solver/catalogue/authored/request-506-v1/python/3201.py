# Original implementation. Contract: https://leetcode.com/problems/find-the-maximum-length-of-valid-subsequence-i/
def solve(nums):
    counts=[0,0];last=-1;alternating=0
    for x in nums:
        p=x%2;counts[p]+=1
        if p!=last:alternating+=1;last=p
    return max(*counts,alternating)
