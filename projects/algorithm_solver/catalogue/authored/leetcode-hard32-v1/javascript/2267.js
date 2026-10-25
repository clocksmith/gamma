'use strict';

// 2267. Check if There Is a Valid Parentheses String Path.
// Balance bitsets use BigInt, not JavaScript's 32-bit shifts; b <= rows + cols.
// O(rows*cols*b) bit work and O(cols*b) bits of working state.
function solve(grid) {
  const rows = grid.length;
  const cols = grid[0].length;
  if ((rows + cols - 1) % 2 !== 0 || grid[0][0] !== '(' || grid[rows - 1][cols - 1] !== ')') {
    return false;
  }
  const balances = Array(cols).fill(0n);
  for (let row = 0; row < rows; row += 1) {
    for (let col = 0; col < cols; col += 1) {
      let incoming = row === 0 && col === 0 ? 1n : balances[col];
      if (col > 0) incoming |= balances[col - 1];
      const reachable = grid[row][col] === '(' ? incoming << 1n : incoming >> 1n;
      const remaining = rows + cols - row - col - 2;
      balances[col] = reachable & ((1n << BigInt(remaining + 1)) - 1n);
    }
  }
  return (balances[cols - 1] & 1n) !== 0n;
}

const hasValidPath = solve;
class Solution {
  hasValidPath(grid) { return solve(grid); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, hasValidPath };
