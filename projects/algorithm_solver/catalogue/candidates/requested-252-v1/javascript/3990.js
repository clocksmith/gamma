/**
 * 3990. Create Grid With Exactly K Paths II
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/create-grid-with-exactly-k-paths-ii/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3990.Create%20Grid%20With%20Exactly%20K%20Paths%20II/README_EN.md
 * Complexity: O(log^2 k) time and output space.
 * A diagonal chain of 2x2 diamonds doubles counts; isolated horizontal exits add selected powers of two to a right-hand collector. For k<=1000 the grid is at most 19x21. Native method unconfirmed.
 */

function solve(k) {
  const bits = k.toString(2).length, height = 2 * bits - 1, width = 2 * bits + 1;
  const grid = Array.from({length: height}, () => Array(width).fill('#'));
  for (let row = 0; row < height; row++) grid[row][width - 1] = '.';
  for (let bit = 0; bit < bits; bit++) {
    const p = 2 * bit;
    grid[p][p] = '.';
    if (bit + 1 < bits) {
      grid[p][p + 1] = '.';
      grid[p + 1][p] = grid[p + 1][p + 1] = '.';
      grid[p + 2][p + 1] = '.';
    }
    if (k & (1 << bit)) for (let col = p + 1; col < width; col++) grid[p][col] = '.';
  }
  return grid.map(row => row.join(''));
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve };
}
