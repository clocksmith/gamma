# Original candidate implementation. Contract: https://leetcode.com/problems/minimum-operations-to-make-median-of-array-equal-to-k/
def solve(nums,k):
    values=sorted(nums); mid=len(values)//2
    return sum(max(0,v-k) for v in values[:mid+1])+sum(max(0,k-v) for v in values[mid:])
