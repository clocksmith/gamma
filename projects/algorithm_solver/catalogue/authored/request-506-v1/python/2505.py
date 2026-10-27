# Original candidate. Contract: https://leetcode.com/problems/bitwise-or-of-all-subsequence-sums/
def solve(nums):
    total=answer=0
    for x in nums:total+=x;answer|=x|total
    return answer
