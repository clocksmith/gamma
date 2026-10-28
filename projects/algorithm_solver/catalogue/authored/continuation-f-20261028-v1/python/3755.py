"""Original frontend 3755 development candidate; qualification unknown."""

def solve(nums):
    earliest = {(0, 0): -1}
    xor = balance = answer = 0
    for i, value in enumerate(nums):
        xor ^= value
        balance += 1 if value % 2 == 0 else -1
        key = (xor, balance)
        if key in earliest:
            answer = max(answer, i - earliest[key])
        else:
            earliest[key] = i
    return answer


class Solution:
    def maxBalancedSubarray(self, nums):
        return solve(nums)
