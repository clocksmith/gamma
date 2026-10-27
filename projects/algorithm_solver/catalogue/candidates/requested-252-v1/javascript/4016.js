/**
 * 4016. Maximum Area of Two Non-Overlapping Square Submatrices
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/maximum-area-of-two-non-overlapping-square-submatrices/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4016.Maximum%20Area%20of%20Two%20Non-Overlapping%20Square%20Submatrices/README_EN.md
 * Complexity: O(m*n) time, O(m+n) auxiliary space.
 * Any two nonoverlapping axis-aligned squares admit a horizontal or vertical separating cut. Bidirectional square DP supplies maxima on both sides; smaller side gives equal-sized squares. Inputs preserved.
 */

function solve(mat) {
  const m = mat.length, n = mat[0].length;
  const rowEnd = new Int32Array(m), colEnd = new Int32Array(n), rowStart = new Int32Array(m), colStart = new Int32Array(n);
  let previous = new Int32Array(n + 1);
  for (let r = 0; r < m; r++) {
    const current = new Int32Array(n + 1);
    for (let c = 0; c < n; c++) if (mat[r][c]) {
      const size = 1 + Math.min(previous[c], previous[c + 1], current[c]);
      current[c + 1] = size; rowEnd[r] = Math.max(rowEnd[r], size); colEnd[c] = Math.max(colEnd[c], size);
    }
    previous = current;
  }
  previous = new Int32Array(n + 1);
  for (let r = m - 1; r >= 0; r--) {
    const current = new Int32Array(n + 1);
    for (let c = n - 1; c >= 0; c--) if (mat[r][c]) {
      const size = 1 + Math.min(previous[c], previous[c + 1], current[c + 1]);
      current[c] = size; rowStart[r] = Math.max(rowStart[r], size); colStart[c] = Math.max(colStart[c], size);
    }
    previous = current;
  }
  let answer = 0;
  for (const [ends, starts] of [[rowEnd, rowStart], [colEnd, colStart]]) {
    for (let i = 1; i < ends.length; i++) ends[i] = Math.max(ends[i], ends[i - 1]);
    for (let i = starts.length - 2; i >= 0; i--) starts[i] = Math.max(starts[i], starts[i + 1]);
    for (let i = 0; i + 1 < ends.length; i++) answer = Math.max(answer, Math.min(ends[i], starts[i + 1]) ** 2);
  }
  return answer;
}

function maxArea(mat) {
  return solve(mat);
}

class Solution {
  maxArea(mat) {
    return solve(mat);
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve, maxArea, Solution };
}
