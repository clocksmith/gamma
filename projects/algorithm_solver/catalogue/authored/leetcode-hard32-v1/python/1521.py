"""1521. Find a Value of a Mysterious Function Closest to Target."""

def solve(arr: list[int], target: int) -> int:
    """O(n*b) time, O(b) space for b-bit inputs; retain distinct suffix AND values."""
    previous = set()
    answer = abs(arr[0] - target)
    for value in arr:
        current = {value}
        for suffix in previous:
            current.add(suffix & value)
        for result in current:
            answer = min(answer, abs(result - target))
        if answer == 0:
            return 0
        previous = current
    return answer


class Solution:
    def closestToTarget(self, arr: list[int], target: int) -> int:
        return solve(arr, target)
