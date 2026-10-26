'use strict';

// 2280. Minimum Lines to Represent a Line Chart: detect slope changes with exact cross products rather than floating division.
// O(n log n) time and O(n) auxiliary space on the bounded coordinate domain; inputs are read-only.
function solve(stockPrices) {
  if (stockPrices.length < 2) return 0;
  const points = stockPrices.slice().sort((left, right) => left[0] - right[0]);
  let previousDx = BigInt(points[1][0] - points[0][0]);
  let previousDy = BigInt(points[1][1] - points[0][1]);
  let lines = 1;
  for (let index = 2; index < points.length; index += 1) {
    const dx = BigInt(points[index][0] - points[index - 1][0]);
    const dy = BigInt(points[index][1] - points[index - 1][1]);
    if (dy * previousDx !== previousDy * dx) lines += 1;
    previousDx = dx;
    previousDy = dy;
  }
  return lines;
}

const minimumLines = solve;
class Solution {
  minimumLines(stockPrices) { return solve(stockPrices); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumLines };
