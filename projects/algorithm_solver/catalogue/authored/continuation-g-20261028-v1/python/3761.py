def solve(nums):
    pending = {}
    answer = len(nums) + 1
    for j, x in enumerate(nums):
        if x in pending:
            answer = min(answer, j - pending[x])
        pending[int(str(x)[::-1])] = j
    return -1 if answer > len(nums) else answer


class Solution:
    def minMirrorPairDistance(self, nums):
        return solve(nums)
