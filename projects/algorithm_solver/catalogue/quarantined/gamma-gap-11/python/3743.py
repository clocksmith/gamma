"""3743. Maximize Cyclic Partition Score."""
from __future__ import annotations


def solve(nums: list[int], k: int) -> int:
    """O(n * min(k, n/2)) time and O(min(k, n/2)) auxiliary space; exact cyclic endpoint-pair dynamic programming."""
    limit = min(k, len(nums) // 2)
    if limit == 0:
        return 0
    answer = 0
    # Each nonzero-range segment has two distinct extremal endpoints. The
    # three states are outside a pair, holding +value, and holding -value.
    # Equal start/end states also admit the single pair crossing the cyclic seam.
    for initial in range(3):
        state = [[float('-inf')] * (limit + 1) for _ in range(3)]
        state[initial][0] = 0
        for value in nums:
            following = [values[:] for values in state]
            for count in range(limit + 1):
                following[1][count] = max(following[1][count], state[0][count] + value)
                following[2][count] = max(following[2][count], state[0][count] - value)
                if count < limit:
                    following[0][count + 1] = max(following[0][count + 1],
                                                 state[1][count] - value,
                                                 state[2][count] + value)
            state = following
        answer = max(answer, max(state[initial]))
    return answer


class Solution:
    def maxScore(self, nums: list[int], k: int) -> int:
        return solve(nums, k)
