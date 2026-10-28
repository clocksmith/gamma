"""Original frontend 3919 variant; qualification unknown."""

def solve(nums, queries):
    n = len(nums)
    closest = [0] * n
    closest[0], closest[-1] = 1, n - 2
    for i in range(1, n - 1):
        closest[i] = i - 1 if nums[i] - nums[i - 1] <= nums[i + 1] - nums[i] else i + 1
    forward, backward = [0], [0]
    for i in range(n - 1):
        gap = nums[i + 1] - nums[i]
        forward.append(forward[-1] + (1 if closest[i] == i + 1 else gap))
        backward.append(backward[-1] + (1 if closest[i + 1] == i else gap))
    return [forward[b] - forward[a] if a <= b else backward[a] - backward[b] for a, b in queries]


class Solution:
    def minCost(self, nums, queries):
        return solve(nums, queries)
