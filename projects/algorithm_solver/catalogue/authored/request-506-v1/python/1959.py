# Original candidate implementation. Contract: https://leetcode.com/problems/minimum-total-space-wasted-with-k-resizing-operations/
def solve(nums, k):
    n = len(nums)
    costs = [[0] * n for _ in nums]
    for i in range(n):
        largest = total = 0
        for j in range(i, n):
            largest = max(largest, nums[j]); total += nums[j]
            costs[i][j] = largest * (j-i+1) - total
    dp = [0] + [float('inf')] * n
    for _ in range(k+1):
        nxt = [0] + [float('inf')] * n
        for end in range(1, n+1):
            nxt[end] = min(dp[start] + costs[start][end-1] for start in range(end))
        dp = nxt
    return dp[n]
