# 523 — Continuous Subarray Sum. Original implementation; authored candidate, not independently qualified.
def solve(nums, k):
    first, current = {0: -1}, 0
    for i, value in enumerate(nums):
        current = (current + value) % k
        if current in first:
            if i - first[current] >= 2:
                return True
        else:
            first[current] = i
    return False

checkSubarraySum = solve

class Solution:
    checkSubarraySum = staticmethod(solve)
