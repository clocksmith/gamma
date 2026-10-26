"""3117. Minimum Sum of Values by Dividing Array.

Rolling DP over segment number and distinct suffix-AND values; O(n*m*B) time and O(m*B) space. Inputs are preserved.
"""

def solve(nums: list[int], andValues: list[int]) -> int:
    m = len(andValues)
    states = {(0, -1): 0}
    for value in nums:
        following = {}
        for (part, previous), price in states.items():
            if part == m:
                continue
            current = previous & value
            target = andValues[part]
            if current & target != target:
                continue
            key = (part, current)
            following[key] = min(following.get(key, float('inf')), price)
            if current == target:
                key = (part + 1, -1)
                following[key] = min(following.get(key, float('inf')), price + value)
        states = following
    return states.get((m, -1), -1)


class Solution:
    def minimumValueSum(self, nums: list[int], andValues: list[int]) -> int:
        return solve(nums, andValues)
