"""Original frontend 466 variant; qualification unknown."""


def solve(s1: str, n1: int, s2: str, n2: int) -> int:
    if not set(s2).issubset(set(s1)):
        return 0
    m = len(s2)
    seen = {}
    history = []
    j = 0
    for block in range(1, n1 + 1):
        for ch in s1:
            if ch == s2[j % m]:
                j += 1
        rem = j % m
        history.append(j)
        if rem in seen:
            prev_block = seen[rem]
            prev_j = history[prev_block - 1]
            cycle_blocks = block - prev_block
            cycle_j = j - prev_j
            remaining = n1 - block
            full_cycles = remaining // cycle_blocks
            tail = remaining % cycle_blocks
            total_j = j + full_cycles * cycle_j + (history[prev_block - 1 + tail] - prev_j)
            return (total_j // m) // n2
        seen[rem] = block
    return (j // m) // n2


getMaxRepetitions = solve


class Solution:
    def getMaxRepetitions(self, s1: str, n1: int, s2: str, n2: int) -> int:
        return solve(s1, n1, s2, n2)
