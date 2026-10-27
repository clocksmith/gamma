/**
 * 3989. Maximum Consistent Columns in a Grid
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/maximum-consistent-columns-in-a-grid/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3989.Maximum%20Consistent%20Columns%20in%20a%20Grid/README_EN.md
 * Complexity: O(m*n^2) time, O(n) space.
 * Longest path in the column-order DAG, with all-row compatibility on every transition. Inputs preserved; native method unconfirmed.
 */

function solve(grid, limit) {
  const n = grid[0].length, best = new Int32Array(n).fill(1);
  let answer = 1;
  for (let right = 0; right < n; right++) {
    for (let left = 0; left < right; left++) {
      if (best[left] < best[right]) continue;
      let valid = true;
      for (const row of grid) if (Math.abs(row[right] - row[left]) > limit) { valid = false; break; }
      if (valid) best[right] = best[left] + 1;
    }
    answer = Math.max(answer, best[right]);
  }
  return answer;
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve };
}
