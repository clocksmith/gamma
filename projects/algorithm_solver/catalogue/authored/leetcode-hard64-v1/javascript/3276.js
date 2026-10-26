'use strict';

// 3276. Select Cells in Grid With Maximum Score: process each value once with a used-row subset state.
// O(S + V*R*2^R) time and O(V + 2^R) auxiliary space. Inputs are preserved.
function solve(grid) {
  const rowsByValue = new Map();
  for (let row = 0; row < grid.length; row += 1) {
    for (const value of grid[row]) rowsByValue.set(value, (rowsByValue.get(value) || 0) | (1 << row));
  }
  const size = 1 << grid.length;
  let best = new Int32Array(size).fill(-1);
  best[0] = 0;
  for (const [value, availableRows] of rowsByValue) {
    const following = best.slice();
    for (let mask = 0; mask < size; mask += 1) {
      if (best[mask] < 0) continue;
      let available = availableRows & ~mask;
      while (available !== 0) {
        const bit = available & -available;
        available -= bit;
        following[mask | bit] = Math.max(following[mask | bit], best[mask] + value);
      }
    }
    best = following;
  }
  let answer = 0;
  for (const value of best) answer = Math.max(answer, value);
  return answer;
}

const maxScore = solve;
class Solution {
  maxScore(grid) { return solve(grid); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxScore };
