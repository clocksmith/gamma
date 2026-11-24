n = int(input())
nums = []
for _ in range(n):
    nums.append(tuple(map(int,input().split())))
# print(nums)
dp = [[10**9]*n for _ in range(n)]
for i in range(n):
    dp[i][i] = 0
# for i in range(n):
#     print(*dp[i])
for l in range(2,n+1):
    for i in range(n-l+1):
        for k in range(l-1):
            # print(l,i,k,dp[i][i+k],dp[i+k+1][i+l-1])
            dp[i][i+l-1] = min(dp[i][i+l-1],dp[i][i+k] + dp[i+k+1][i+l-1] + nums[i][0]*nums[i+k][1]*nums[i+l-1][1])
print(dp[0][n-1])
# for i in range(n):
#     print(*dp[i])

