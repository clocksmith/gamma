"""Original candidate; no qualification or admission."""

def solve(nums,limit):
    delta=[0]*(2*limit+3)
    for i in range(len(nums)//2):
        a,b=nums[i],nums[-1-i];delta[2]+=2;delta[1+min(a,b)]-=1;delta[a+b]-=1;delta[a+b+1]+=1;delta[limit+max(a,b)+1]+=1
    current=0;answer=len(nums)
    for total in range(2,2*limit+1):current+=delta[total];answer=min(answer,current)
    return answer


class Solution:
    def minMoves(self, nums, limit):
        return solve(nums, limit)
