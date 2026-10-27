# Original candidate implementation. Contract: https://leetcode.com/problems/earliest-second-to-mark-indices-i/
def solve(nums,changeIndices):
    n=len(nums);m=len(changeIndices)
    def feasible(seconds):
        last=[-1]*n
        for t in range(seconds):last[changeIndices[t]-1]=t
        if -1 in last:return False
        free=0
        for t in range(seconds):
            i=changeIndices[t]-1
            if last[i]==t:
                if free<nums[i]:return False
                free-=nums[i]
            else:free+=1
        return True
    if not feasible(m):return -1
    lo,hi=1,m
    while lo<hi:
        mid=(lo+hi)//2
        if feasible(mid):hi=mid
        else:lo=mid+1
    return lo
