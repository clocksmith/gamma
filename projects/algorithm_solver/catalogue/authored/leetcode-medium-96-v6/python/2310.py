"""2310. Sum of Numbers With Units Digit K: find the first feasible count among one complete cycle of final digits."""


def solve(num: int, k: int) -> int:
    """O(1) time and O(1) auxiliary space; inputs are read-only."""
    if num == 0:
        return 0
    for count in range(1, 11):
        if count * k <= num and (num - count * k) % 10 == 0:
            return count
    return -1


class Solution:
    def minimumNumbers(self, num: int, k: int) -> int:
        return solve(num, k)
