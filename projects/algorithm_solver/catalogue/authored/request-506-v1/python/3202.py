# Original candidate implementation. Contract: https://leetcode.com/problems/find-the-maximum-length-of-valid-subsequence-ii/
def solve(nums,k):
    dp=[[0]*k for _ in range(k)];answer=0
    for value in nums:
        r=value%k
        for previous in range(k):
            dp[r][previous]=dp[previous][r]+1
            answer=max(answer,dp[r][previous])
    return answer
