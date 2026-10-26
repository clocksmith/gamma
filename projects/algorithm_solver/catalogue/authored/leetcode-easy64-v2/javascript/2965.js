'use strict';

// 2965. Find Missing and Repeated Values (Easy).
// Specification: https://leetcode.com/problems/find-missing-and-repeated-values/description/
// O(n^2) time and space; return repeated then missing; preserve grid and row identities.
function solve(grid) {
  const count = grid.length * grid.length;
  const seen = new Array(count + 1).fill(false);
  let repeated = -1;
  for (const row of grid) {
    for (const value of row) {
      if (seen[value]) repeated = value;
      seen[value] = true;
    }
  }
  for (let value = 1; value <= count; value++) {
    if (!seen[value]) return [repeated, value];
  }
  return [-1, -1];
}

const findMissingAndRepeatedValues = solve;
class Solution {
  findMissingAndRepeatedValues(grid) { return solve(grid); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findMissingAndRepeatedValues };
