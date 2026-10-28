"""481. Magical String (Medium).

Specification: https://leetcode.com/problems/magical-string/description/
"""


def solve(n: int) -> int:
    if n == 0:
        return 0
    sequence = [1, 2, 2]
    index = 2
    while len(sequence) < n:
        count = sequence[index]
        next_value = 2 if sequence[-1] == 1 else 1
        for _i in range(count):
            if len(sequence) >= n:
                break
            sequence.append(next_value)
        index += 1
    return sum(1 for i in range(n) if sequence[i] == 1)


class Solution:
    def magicalString(self, n: int) -> int:
        return solve(n)
