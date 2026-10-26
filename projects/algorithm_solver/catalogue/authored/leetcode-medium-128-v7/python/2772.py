"""2772. Apply Operations to Make All Array Elements Equal to Zero: start exactly the decrements needed at each index and expire them after k positions."""


def solve(nums: list[int], k: int) -> bool:
    """O(n) time and O(n) auxiliary space; inputs are read-only."""
    changes = [0] * (len(nums) + 1)
    active = 0
    for index, value in enumerate(nums):
        active += changes[index]
        needed = value - active
        if needed < 0:
            return False
        if needed:
            if index + k > len(nums):
                return False
            active += needed
            changes[index + k] -= needed
    return True


class Solution:
    def checkArray(self, nums: list[int], k: int) -> bool:
        return solve(nums, k)
