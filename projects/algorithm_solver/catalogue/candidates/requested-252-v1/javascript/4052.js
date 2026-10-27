/**
 * 4052. Cyclically Shift Rows and Columns
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/cyclically-shift-rows-and-columns/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4052.Cyclically%20Shift%20Rows%20and%20Columns/README_EN.md
 * Complexity: O(n^2) time and output space.
 * Apply column displacement using the already-shifted column index. All inputs preserved.
 */

function solve(n,grid,rowShift,colShift) {
  const answer=Array.from({length:n},()=>Array(n).fill(0));
  for(let row=0;row<n;row++)for(let col=0;col<n;col++) {
    const c=(col-rowShift[row]+n)%n,r=(row-colShift[c]+n)%n;
    answer[r][c]=grid[row][col];
  }
  return answer;
}

function cyclicShift(n, grid, rowShift, colShift) {
  return solve(n, grid, rowShift, colShift);
}

class Solution {
  cyclicShift(n, grid, rowShift, colShift) {
    return solve(n, grid, rowShift, colShift);
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve, cyclicShift, Solution };
}
