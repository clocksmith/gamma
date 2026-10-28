"""Original frontend 3858 variant; qualification unknown."""

def solve(grid):
    allowed = (1 << 17) - 1
    for bit in range(16, -1, -1):
        trial = allowed & ~(1 << bit)
        if all(any(value & ~trial == 0 for value in row) for row in grid):
            allowed = trial
    return allowed


class Solution:
    def minimumOR(self, grid):
        return solve(grid)
