"""Original frontend 3942 variant; qualification unknown."""

def solve(nums):
    n = len(nums)
    zero = nums.index(0)
    answer = n + 3
    if all(nums[(zero + i) % n] == i for i in range(n)):
        answer = min(zero, n - zero + 2)
    if all(nums[(zero - i) % n] == i for i in range(n)):
        rotations = n - 1 - zero
        answer = min(answer, 1 + min(rotations, n - rotations))
    return answer if answer <= n + 2 else -1


class Solution:
    def minOperations(self, nums):
        return solve(nums)
