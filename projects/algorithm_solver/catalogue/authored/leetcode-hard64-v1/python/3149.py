"""3149. Find the Minimum Cost Array Permutation: subset dynamic programming and lexicographic reconstruction."""

from array import array


def solve(nums: list[int]) -> list[int]:
    """O(n^2 * 2^n) time and O(n * 2^n) auxiliary space. Inputs are preserved."""
    n = len(nums)
    full = (1 << n) - 1
    memo = array('i', [-1]) * ((1 << n) * n)

    def best(mask, last):
        if mask == full:
            return abs(last - nums[0])
        key = mask * n + last
        if memo[key] != -1:
            return memo[key]
        value = n * n
        for following in range(1, n):
            if not mask & (1 << following):
                value = min(value, abs(last - nums[following]) + best(mask | (1 << following), following))
        memo[key] = value
        return value

    # Every cycle can be rotated to start with zero without changing its score.
    answer = [0]
    mask = 1
    last = 0
    while mask != full:
        remaining = best(mask, last)
        for following in range(1, n):
            if mask & (1 << following):
                continue
            candidate = abs(last - nums[following]) + best(mask | (1 << following), following)
            if candidate == remaining:
                answer.append(following)
                mask |= 1 << following
                last = following
                break
    return answer


class Solution:
    def findPermutation(self, nums: list[int]) -> list[int]:
        return solve(nums)
