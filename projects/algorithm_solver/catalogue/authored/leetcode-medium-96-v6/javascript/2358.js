'use strict';

// 2358. Maximum Number of Groups Entering a Competition: find the largest triangular group count since sorted positive grades can realize it.
// O(log(n + 1)) time and O(1) auxiliary space; inputs are read-only.
function solve(grades) {
  // Sorting conceptually yields groups of sizes 1, 2, ... with increasing sums.
  const size = grades.length;
  let low = 0;
  let high = size;
  while (low < high) {
    const middle = Math.floor((low + high + 1) / 2);
    if (middle * (middle + 1) / 2 <= size) low = middle;
    else high = middle - 1;
  }
  return low;
}

const maximumGroups = solve;
class Solution {
  maximumGroups(grades) { return solve(grades); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximumGroups };
