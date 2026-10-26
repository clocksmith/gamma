'use strict';

// 3219. Minimum Cost for Cutting Cake II.
// Take the most expensive remaining cut before multiplying perpendicular pieces; O(m log m+n log n) time and O(m+n) space. Inputs are preserved.

function solve(m, n, horizontalCut, verticalCut) {
  const horizontal = horizontalCut.slice().sort((a, b) => b - a);
  const vertical = verticalCut.slice().sort((a, b) => b - a);
  let first = 0, second = 0, answer = 0;
  while (first < horizontal.length || second < vertical.length) {
    if (second === vertical.length || (first < horizontal.length && horizontal[first] >= vertical[second])) {
      answer += horizontal[first] * (second + 1);
      first += 1;
    } else {
      answer += vertical[second] * (first + 1);
      second += 1;
    }
  }
  return answer;
}

const minimumCost = solve;
class Solution {
  minimumCost(m, n, horizontalCut, verticalCut) { return solve(m, n, horizontalCut, verticalCut); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumCost };
