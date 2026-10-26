"""1404. Number of Steps to Reduce a Number in Binary Representation to One: scan low bits while carrying additions instead of parsing a large integer."""


def solve(s: str) -> int:
    """O(n) time and O(1) auxiliary space; inputs are read-only."""
    carry = steps = 0
    for index in range(len(s) - 1, 0, -1):
        bit = ord(s[index]) - ord('0') + carry
        if bit == 1:
            steps += 2
            carry = 1
        else:
            steps += 1
    return steps + carry


class Solution:
    def numSteps(self, s: str) -> int:
        return solve(s)
