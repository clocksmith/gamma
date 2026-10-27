# Original candidate implementation. Contract: https://leetcode.com/problems/maximum-number-of-removal-queries-that-can-be-processed-i/
def solve(nums,queries):
    n=len(nums);m=len(queries);dp=[[-1]*n for _ in range(n)];dp[0][n-1]=0;answer=0
    for length in range(n,0,-1):
        for left in range(n-length+1):
            right=left+length-1;t=dp[left][right]
            if t<0:continue
            if t==m:return m
            a=t+int(nums[left]>=queries[t]);b=t+int(nums[right]>=queries[t]);answer=max(answer,a,b)
            if length>1:
                dp[left+1][right]=max(dp[left+1][right],a)
                dp[left][right-1]=max(dp[left][right-1],b)
    return answer
