"""2267. Check if There Is a Valid Parentheses String Path."""

def solve(grid: list[list[str]]) -> bool:
    """Row DP with arbitrary-width balance bitsets; O(rows*cols*b) bit work, O(cols*b) bits."""
    rows, cols = len(grid), len(grid[0])
    if (rows + cols - 1) % 2 or grid[0][0] != '(' or grid[-1][-1] != ')':
        return False
    balances = [0] * cols
    for row in range(rows):
        for col in range(cols):
            incoming = 1 if row == 0 and col == 0 else balances[col]
            if col:
                incoming |= balances[col - 1]
            reachable = incoming << 1 if grid[row][col] == '(' else incoming >> 1
            remaining = rows + cols - row - col - 2
            # Discard negative balances and balances too large to close before the end.
            balances[col] = reachable & ((1 << (remaining + 1)) - 1)
    return bool(balances[-1] & 1)


class Solution:
    def hasValidPath(self, grid: list[list[str]]) -> bool:
        return solve(grid)
