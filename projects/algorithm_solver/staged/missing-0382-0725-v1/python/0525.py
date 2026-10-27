"""525. Contiguous Array."""

def solve(nums: list[int]) -> int:
    first = {0: -1}
    balance = answer = 0
    for i, value in enumerate(nums):
        balance += 1 if value else -1
        if balance in first:
            answer = max(answer, i - first[balance])
        else:
            first[balance] = i
    return answer


class Solution:
    def findMaxLength(self, nums: list[int]) -> int:
        return solve(nums)
