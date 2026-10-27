# Original candidate. Contract: https://leetcode.com/problems/largest-element-in-an-array-after-merge-operations/
def solve(nums):
    total=answer=nums[-1]
    for x in reversed(nums[:-1]):total=total+x if x<=total else x;answer=max(answer,total)
    return answer
