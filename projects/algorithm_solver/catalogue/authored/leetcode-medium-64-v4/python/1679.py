"""1679. Max Number of K-Sum Pairs: consume an unmatched complement before storing each value."""


def solve(nums: list[int], k: int) -> int:
    """O(n) expected time and O(n) auxiliary space; inputs are read-only."""
    unmatched = {}
    pairs = 0
    for value in nums:
        complement = k - value
        count = unmatched.get(complement, 0)
        if count:
            if count == 1:
                del unmatched[complement]
            else:
                unmatched[complement] = count - 1
            pairs += 1
        else:
            unmatched[value] = unmatched.get(value, 0) + 1
    return pairs


class Solution:
    def maxOperations(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
