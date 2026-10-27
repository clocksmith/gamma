# Original candidate. Contract: https://leetcode.com/problems/ways-to-split-array-into-good-subarrays/
def solve(nums):
    last=-1;answer=1
    for i,x in enumerate(nums):
        if x:
            if last>=0:answer=answer*(i-last)%1000000007
            last=i
    return answer if last>=0 else 0
