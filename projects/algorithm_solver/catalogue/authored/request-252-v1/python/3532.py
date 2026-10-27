def solve(n, nums, maxDiff, queries):
    component = [0] * n
    for i in range(1, n):
        component[i] = component[i - 1] + (nums[i] - nums[i - 1] > maxDiff)
    return [component[u] == component[v] for u, v in queries]
