def solve(nums):
    sign = 1
    answer = 0
    for i, x in enumerate(nums):
        if x % 2:
            sign = -sign
        if i % 6 == 5:
            sign = -sign
        answer += sign * x
    return answer


class Solution:
    def scoreDifference(self, nums):
        return solve(nums)
