"""2429. Minimize XOR: match the highest valuable set bits first and place remaining bits at the bottom."""


def solve(num1: int, num2: int) -> int:
    """O(31) time and O(1) auxiliary space on the nonnegative 31-bit domain; inputs are read-only."""
    remaining = num2.bit_count()
    answer = 0
    for bit in range(30, -1, -1):
        mask = 1 << bit
        if remaining and num1 & mask:
            answer |= mask
            remaining -= 1
    for bit in range(31):
        mask = 1 << bit
        if remaining and not answer & mask:
            answer |= mask
            remaining -= 1
    return answer


class Solution:
    def minimizeXor(self, num1: int, num2: int) -> int:
        return solve(num1, num2)
