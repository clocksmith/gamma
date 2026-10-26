"""3621. Number of Integers With Popcount-Depth Equal to K I.

Count bounded bit strings by population count and classify exact reduction depth, treating one separately; O(log^2 n) arithmetic operations and space. Inputs are preserved.
"""

def solve(n: int, k: int) -> int:
    if n < 1:
        return 0
    if k == 0:
        return 1
    digits = bin(n)[2:]
    length = len(digits)
    choose = [[1]]
    for row in range(1, length + 1):
        previous = choose[-1]
        choose.append([1] + [previous[index - 1] + previous[index] for index in range(1, row)] + [1])
    counts = [0] * (length + 1)
    ones = 0
    for index, character in enumerate(digits):
        if character == '1':
            remaining = length - index - 1
            for extra in range(remaining + 1):
                counts[ones + extra] += choose[remaining][extra]
            ones += 1
    counts[ones] += 1
    depth = [0] * (length + 1)
    for value in range(2, length + 1):
        depth[value] = 1 + depth[value.bit_count()]
    answer = sum(counts[value] for value in range(1, length + 1) if 1 + depth[value] == k)
    return answer - int(k == 1)


class Solution:
    def popcountDepth(self, n: int, k: int) -> int:
        return solve(n, k)
