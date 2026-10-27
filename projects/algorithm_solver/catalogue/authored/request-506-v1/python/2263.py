# Original implementation. Contract: https://leetcode.com/problems/make-array-non-decreasing-or-non-increasing/
def solve(nums):
    def cost(a):
        dp=[0]*1001
        for x in a:
            best=10**18;new=[]
            for y,v in enumerate(dp):best=min(best,v);new.append(best+abs(x-y))
            dp=new
        return min(dp)
    return min(cost(nums),cost(nums[::-1]))
