# Original candidate implementation. Contract: https://leetcode.com/problems/sum-of-digit-differences-of-all-pairs/
def solve(nums):
    width=len(str(nums[0])); counts=[[0]*10 for _ in range(width)];answer=0
    for seen,v in enumerate(nums):
        for pos,ch in enumerate(str(v)):
            digit=int(ch); answer+=seen-counts[pos][digit];counts[pos][digit]+=1
    return answer
