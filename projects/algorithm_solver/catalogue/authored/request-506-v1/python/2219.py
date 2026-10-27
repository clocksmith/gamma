# Original candidate implementation. Contract: https://leetcode.com/problems/maximum-sum-score-of-array/
def solve(nums):
    total=sum(nums);prefix=0;answer=float('-inf')
    for x in nums:
        answer=max(answer,total-prefix);prefix+=x;answer=max(answer,prefix)
    return answer
