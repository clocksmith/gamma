"""3533. Concatenated Divisibility.

Memoize subset/remainder feasibility and reconstruct by trying unused values in numeric order; O(n*k*2^n) time and O(k*2^n+n) space. Inputs are preserved.
"""

def solve(nums: list[int], k: int) -> list[int]:
    values = sorted(nums)
    if k == 1:
        return values
    n, full = len(values), (1 << len(values)) - 1
    factors = [pow(10, len(str(value)), k) for value in values]
    memo = bytearray((1 << n) * k)

    def possible(mask, remainder):
        if mask == full:
            return remainder == 0
        identity = mask * k + remainder
        if memo[identity]:
            return memo[identity] == 2
        for index, value in enumerate(values):
            if mask & (1 << index):
                continue
            following = (remainder * factors[index] + value) % k
            if possible(mask | (1 << index), following):
                memo[identity] = 2
                return True
        memo[identity] = 1
        return False

    if not possible(0, 0):
        return []
    answer = []
    mask = remainder = 0
    while mask != full:
        for index, value in enumerate(values):
            if mask & (1 << index):
                continue
            following = (remainder * factors[index] + value) % k
            if possible(mask | (1 << index), following):
                answer.append(value)
                mask |= 1 << index
                remainder = following
                break
    return answer


class Solution:
    def concatenatedDivisibility(self, nums: list[int], k: int) -> list[int]:
        return solve(nums, k)
