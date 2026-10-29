"""Original candidate; no qualification or admission."""

def solve(target,mountainArr):
    cache={}
    def get(i):
        if i not in cache:cache[i]=mountainArr.get(i)
        return cache[i]
    n=mountainArr.length();left,right=0,n-1
    while left<right:
        mid=(left+right)//2
        if get(mid)<get(mid+1):left=mid+1
        else:right=mid
    peak=left
    for lo,hi,ascending in ((0,peak,True),(peak+1,n-1,False)):
        left,right=lo,hi
        while left<=right:
            mid=(left+right)//2;value=get(mid)
            if value==target:return mid
            if (value<target)==ascending:left=mid+1
            else:right=mid-1
    return -1


class Solution:
    def findInMountainArray(self, target, mountainArr):
        return solve(target, mountainArr)
