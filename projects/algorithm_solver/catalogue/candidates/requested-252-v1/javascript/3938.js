/**
 * 3938. Maximum Path Intersection Sum in a Grid
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/maximum-path-intersection-sum-in-a-grid/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3938.Maximum%20Path%20Intersection%20Sum%20in%20a%20Grid/README_EN.md
 * Complexity: O(rows*columns) time, O(1) auxiliary space.
 * Both dimensions >=2. Shared cells at distinct columns must have equal rows (opposite vertical monotonicity); otherwise all shared cells are vertical. Boundary singleton intersections are impossible; interior singletons and all length>=2 straight segments are realizable. Native name pending.
 */

function solve(grid) {
  const rows = grid.length;
  const columns = grid[0].length;
  let answer = -Infinity;
  for (let row = 0; row < rows; row += 1) {
    let ending = grid[row][0];
    for (let column = 1; column < columns; column += 1) {
      answer = Math.max(answer, ending + grid[row][column]);
      ending = Math.max(grid[row][column], ending + grid[row][column]);
    }
    if (row > 0 && row + 1 < rows) {
      for (let column = 1; column + 1 < columns; column += 1) answer = Math.max(answer, grid[row][column]);
    }
  }
  for (let column = 0; column < columns; column += 1) {
    let ending = grid[0][column];
    for (let row = 1; row < rows; row += 1) {
      answer = Math.max(answer, ending + grid[row][column]);
      ending = Math.max(grid[row][column], ending + grid[row][column]);
    }
  }
  return answer;
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve };
}
