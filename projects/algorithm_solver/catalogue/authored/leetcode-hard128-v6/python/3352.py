"""3352. Count K-Reducible Numbers Less Than N.

Count smaller binary strings by population count, then classify reduction depth; O(L^2) time and space. Inputs are preserved.
"""

def solve(s: str, k: int) -> int:
    modulus = 1_000_000_007
    if k == 0:
        return int(len(s) > 1)
    length = len(s)
    choose = [[1]]
    for row in range(1, length + 1):
        previous = choose[-1]
        choose.append([1] + [(previous[index - 1] + previous[index]) % modulus for index in range(1, row)] + [1])
    counts = [0] * (length + 1)
    ones = 0
    for index, character in enumerate(s):
        if character == '1':
            remaining = length - index - 1
            for extra in range(remaining + 1):
                counts[ones + extra] = (counts[ones + extra] + choose[remaining][extra]) % modulus
            ones += 1
    depth = [0] * (length + 1)
    for value in range(2, length + 1):
        depth[value] = 1 + depth[value.bit_count()]
    return sum(counts[value] for value in range(1, length + 1) if 1 + depth[value] <= k) % modulus


class Solution:
    def countKReducibleNumbers(self, s: str, k: int) -> int:
        return solve(s, k)
