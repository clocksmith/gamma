"""873. Length of Longest Fibonacci Subsequence: extend subsequences indexed by their last two positions."""


def solve(arr: list[int]) -> int:
    """O(n^2) expected time and O(n^2) auxiliary space; inputs are read-only."""
    size = len(arr)
    positions = {value: index for index, value in enumerate(arr)}
    lengths = [[0] * size for _ in arr]
    answer = 0
    for right in range(size):
        for middle in range(right):
            needed = arr[right] - arr[middle]
            if needed >= arr[middle]:
                continue
            left = positions.get(needed)
            if left is not None:
                lengths[middle][right] = (lengths[left][middle] or 2) + 1
                answer = max(answer, lengths[middle][right])
    return answer


class Solution:
    def lenLongestFibSubseq(self, arr: list[int]) -> int:
        return solve(arr)
