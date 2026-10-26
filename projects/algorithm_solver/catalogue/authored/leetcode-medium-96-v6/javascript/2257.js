'use strict';

// 2257. Count Unguarded Cells in the Grid: sweep visibility in four directions while walls interrupt and guards restart each ray.
// O(m * n + g + w) time and O(m * n) auxiliary space; inputs are read-only.
function solve(m, n, guards, walls) {
  const cells = new Uint8Array(m * n);
  const visible = new Uint8Array(m * n);
  for (const [row, column] of walls) cells[row * n + column] = 1;
  for (const [row, column] of guards) cells[row * n + column] = 2;
  function sweep(start, step, count) {
    let active = false;
    let index = start;
    for (let offset = 0; offset < count; offset += 1) {
      if (cells[index]) active = cells[index] === 2;
      else if (active) visible[index] = 1;
      index += step;
    }
  }
  for (let row = 0; row < m; row += 1) {
    sweep(row * n, 1, n);
    sweep(row * n + n - 1, -1, n);
  }
  for (let column = 0; column < n; column += 1) {
    sweep(column, n, m);
    sweep((m - 1) * n + column, -n, m);
  }
  let answer = 0;
  for (let index = 0; index < cells.length; index += 1) {
    if (cells[index] === 0 && visible[index] === 0) answer += 1;
  }
  return answer;
}

const countUnguarded = solve;
class Solution {
  countUnguarded(m, n, guards, walls) { return solve(m, n, guards, walls); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countUnguarded };
