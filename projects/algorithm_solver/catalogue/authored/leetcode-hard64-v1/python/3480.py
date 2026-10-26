"""3480. Maximize Subarrays After Removing One Conflicting Pair: sweep the two strongest forbidden left endpoints and accumulate removal gains."""


def solve(n: int, conflictingPairs: list[list[int]]) -> int:
    """O(n + q) time and O(n + q) auxiliary space. Inputs are preserved."""
    ending = [[] for _ in range(n + 1)]
    for index, pair in enumerate(conflictingPairs):
        first, second = min(pair), max(pair)
        ending[second].append((first, index))
    gain = [0] * len(conflictingPairs)
    largest = second_largest = 0
    owner = -1
    base = 0
    for right in range(1, n + 1):
        for left, index in ending[right]:
            if left > largest:
                second_largest = largest
                largest = left
                owner = index
            elif left > second_largest:
                second_largest = left
        base += right - largest
        if owner >= 0:
            gain[owner] += largest - second_largest
    return base + max(gain, default=0)


class Solution:
    def maxSubarrays(self, n: int, conflictingPairs: list[list[int]]) -> int:
        return solve(n, conflictingPairs)
