/**
 * 3963. Create Grid With Exactly One Path
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/create-grid-with-exactly-one-path/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3963.Create%20Grid%20With%20Exactly%20One%20Path/README_EN.md
 * Complexity: O(m*n) output time and space.
 * Returns one valid construction, not necessarily the example grid. Only the top row and final column are open.
 */

function solve(m, n) {
  return ['.'.repeat(n), ...Array.from({ length: m - 1 }, () => '#'.repeat(n - 1) + '.')];
}

function createGrid(m, n) {
  return solve(m, n);
}

class Solution {
  createGrid(m, n) {
    return solve(m, n);
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve, createGrid, Solution };
}
