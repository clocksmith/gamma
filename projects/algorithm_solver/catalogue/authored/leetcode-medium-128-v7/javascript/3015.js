'use strict';

// 3015. Count the Number of Houses at a Certain Distance I: compare the direct path with each orientation of the extra edge.
// O(n * n) time and O(n) auxiliary space; inputs are read-only.
function solve(n, x, y) {
  const counts = new Array(n).fill(0);
  for (let left = 1; left <= n; left += 1) {
    for (let right = left + 1; right <= n; right += 1) {
      const distance = Math.min(right - left,
        Math.abs(left - x) + 1 + Math.abs(right - y),
        Math.abs(left - y) + 1 + Math.abs(right - x));
      counts[distance - 1] += 2;
    }
  }
  return counts;
}

const countOfPairs = solve;
class Solution {
  countOfPairs(n, x, y) { return solve(n, x, y); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countOfPairs };
