'use strict';

// 3933. Largest Local Values in a Matrix II.
// Specification: https://leetcode.com/problems/largest-local-values-in-a-matrix-ii/description/
// O(V*rows*columns) time and O(rows*columns) space, at most 200 distinct positive values. Inputs are preserved.
function solve(matrix) {
  const rows = matrix.length;
  const columns = matrix[0].length;
  const groups = new Map();
  for (let row = 0; row < rows; row++) for (let column = 0; column < columns; column++) {
    const value = matrix[row][column];
    if (value === 0) continue;
    if (!groups.has(value)) groups.set(value, []);
    groups.get(value).push([row, column]);
  }
  let answer = 0;
  for (const [value, cells] of groups) {
    const prefix = Array.from({ length: rows + 1 }, () => new Int32Array(columns + 1));
    for (let row = 0; row < rows; row++) {
      let running = 0;
      for (let column = 0; column < columns; column++) {
        if (matrix[row][column] > value) running++;
        prefix[row + 1][column + 1] = prefix[row][column + 1] + running;
      }
    }
    for (const [row, column] of cells) {
      const top = Math.max(0, row - value);
      const bottom = Math.min(rows - 1, row + value);
      const left = Math.max(0, column - value);
      const right = Math.min(columns - 1, column + value);
      let larger = prefix[bottom + 1][right + 1] - prefix[top][right + 1] - prefix[bottom + 1][left] + prefix[top][left];
      for (const r of [row - value, row + value]) for (const c of [column - value, column + value]) {
        if (r >= 0 && r < rows && c >= 0 && c < columns && matrix[r][c] > value) larger--;
      }
      if (larger === 0) answer++;
    }
  }
  return answer;
}

if (typeof module !== 'undefined') module.exports = { solve };
