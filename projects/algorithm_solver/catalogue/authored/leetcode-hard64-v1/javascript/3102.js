'use strict';

// 3102. Minimize Manhattan Distances: remove only an extremal point in rotated coordinates.
// O(n) time and O(1) auxiliary space. Inputs are preserved.
function solve(points) {
  let minimumSum = 0;
  let maximumSum = 0;
  let minimumDifference = 0;
  let maximumDifference = 0;
  for (let index = 0; index < points.length; index += 1) {
    const [x, y] = points[index];
    if (x + y < points[minimumSum][0] + points[minimumSum][1]) minimumSum = index;
    if (x + y > points[maximumSum][0] + points[maximumSum][1]) maximumSum = index;
    if (x - y < points[minimumDifference][0] - points[minimumDifference][1]) minimumDifference = index;
    if (x - y > points[maximumDifference][0] - points[maximumDifference][1]) maximumDifference = index;
  }
  let answer = Infinity;
  for (const removed of new Set([minimumSum, maximumSum, minimumDifference, maximumDifference])) {
    let lowSum = Infinity;
    let highSum = -Infinity;
    let lowDifference = Infinity;
    let highDifference = -Infinity;
    for (let index = 0; index < points.length; index += 1) {
      if (index === removed) continue;
      const [x, y] = points[index];
      lowSum = Math.min(lowSum, x + y);
      highSum = Math.max(highSum, x + y);
      lowDifference = Math.min(lowDifference, x - y);
      highDifference = Math.max(highDifference, x - y);
    }
    answer = Math.min(answer, Math.max(highSum - lowSum, highDifference - lowDifference));
  }
  return answer;
}

const minimumDistance = solve;
class Solution {
  minimumDistance(points) { return solve(points); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumDistance };
