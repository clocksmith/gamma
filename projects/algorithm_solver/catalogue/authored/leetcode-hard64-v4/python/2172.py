"""2172. Maximum AND Sum of Array."""


def solve(nums: list[int], numSlots: int) -> int:
    """Base-three slot-occupancy DP; O(S*3^S) time and O(3^S) space. Inputs are preserved."""
    powers = [3 ** slot for slot in range(numSlots)]
    states = 3 ** numSlots
    best = [-1] * states
    best[0] = 0
    answer = 0
    for state in range(states):
        if best[state] < 0:
            continue
        remaining = state
        occupied = 0
        digits = []
        for _ in range(numSlots):
            remaining, digit = divmod(remaining, 3)
            occupied += digit
            digits.append(digit)
        if occupied == len(nums):
            answer = max(answer, best[state])
            continue
        for slot in range(numSlots):
            if digits[slot] < 2:
                following = state + powers[slot]
                best[following] = max(best[following], best[state] + (nums[occupied] & (slot + 1)))
    return answer


class Solution:
    def maximumANDSum(self, nums: list[int], numSlots: int) -> int:
        return solve(nums, numSlots)
