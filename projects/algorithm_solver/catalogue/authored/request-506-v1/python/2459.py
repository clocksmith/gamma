# Original candidate. Contract: https://leetcode.com/problems/sort-array-by-moving-items-to-empty-space/
def solve(nums):
    n=len(nums);blank=nums.index(0)
    def cost(shift):
        seen=[False]*n;answer=0
        for start in range(n):
            if seen[start]:continue
            i=start;length=0;has_blank=False
            while not seen[i]:
                seen[i]=True;length+=1;has_blank|=i==blank;i=(nums[i]-shift)%n
            if length>1:answer+=length-1 if has_blank else length+1
        return answer
    return min(cost(0),cost(1))
