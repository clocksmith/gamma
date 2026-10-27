"""390. Elimination Game. Track the arithmetic progression of surviving values."""

def solve(n: int) -> int:
    head, step, remaining = 1, 1, n
    left_to_right = True
    while remaining > 1:
        if left_to_right or remaining % 2:
            head += step
        remaining //= 2
        step *= 2
        left_to_right = not left_to_right
    return head


class Solution:
    def lastRemaining(self, n: int) -> int:
        return solve(n)
