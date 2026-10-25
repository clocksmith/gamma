"""1471. The k Strongest Values in an Array: take the stronger sorted endpoint with larger-value ties."""


def solve(arr: list[int], k: int) -> list[int]:
    """O(n log n + k) time and O(n) auxiliary space; inputs are read-only."""
    values = sorted(arr)
    median = values[(len(values) - 1) // 2]
    left = 0
    right = len(values) - 1
    answer = []
    while len(answer) < k:
        if median - values[left] > values[right] - median:
            answer.append(values[left])
            left += 1
        else:
            answer.append(values[right])
            right -= 1
    return answer


class Solution:
    def getStrongest(self, arr: list[int], k: int) -> list[int]:
        return solve(arr, k)
