'use strict';

// 2088. Count Fertile Pyramids in a Land. Two directional height DPs; O(R*C) time and O(C) auxiliary space. Inputs are preserved.

function solve(grid) {
  const rows = grid.length;
  const columns = grid[0].length;
  let answer = 0;
  for (const direction of [1, -1]) {
    let previous = new Int32Array(columns);
    for (let step = 0; step < rows; step += 1) {
      const row = direction === 1 ? step : rows - 1 - step;
      const current = new Int32Array(columns);
      for (let column = 0; column < columns; column += 1) {
        if (grid[row][column] === 0) continue;
        current[column] = 1;
        if (column > 0 && column + 1 < columns) {
          current[column] += Math.min(previous[column - 1], previous[column], previous[column + 1]);
        }
        answer += current[column] - 1;
      }
      previous = current;
    }
  }
  return answer;
}

const countPyramids = solve;
class Solution {
  countPyramids(grid) { return solve(grid); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countPyramids };
