'use strict';

// 1937. Maximum Number of Points with Cost: propagate the best previous-row score from both directions.
// O(rows * columns) time and O(columns) auxiliary space; inputs are read-only.
function solve(points) {
  const columns = points[0].length;
  let previous = points[0].slice();
  for (let row = 1; row < points.length; row += 1) {
    const next = new Array(columns);
    let best = previous[0];
    for (let column = 0; column < columns; column += 1) {
      best = Math.max(best - 1, previous[column]);
      next[column] = points[row][column] + best;
    }
    best = previous[columns - 1];
    for (let column = columns - 1; column >= 0; column -= 1) {
      best = Math.max(best - 1, previous[column]);
      next[column] = Math.max(next[column], points[row][column] + best);
    }
    previous = next;
  }
  let result = previous[0];
  for (const value of previous) result = Math.max(result, value);
  return result;
}

const maxPoints = solve;
class Solution {
  maxPoints(points) { return solve(points); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxPoints };
