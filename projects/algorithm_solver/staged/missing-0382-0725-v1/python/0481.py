"""481. Magical String."""

def solve(n: int) -> int:
    if n <= 0:
        return 0
    sequence = [1, 2, 2]
    head = 2
    next_value = 1
    while len(sequence) < n:
        sequence.extend([next_value] * sequence[head])
        next_value = 3 - next_value
        head += 1
    return sequence[:n].count(1)


class Solution:
    def magicalString(self, n: int) -> int:
        return solve(n)
