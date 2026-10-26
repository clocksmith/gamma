'use strict';

// 3285. Find Indices of Stable Mountains (Easy).
// Specification: https://leetcode.com/problems/find-indices-of-stable-mountains/description/
// O(n) time and output space; a mountain depends on its predecessor, not itself.
function solve(height, threshold) {
  const result = [];
  for (let index = 1; index < height.length; index++) {
    if (height[index - 1] > threshold) result.push(index);
  }
  return result;
}

const stableMountains = solve;
class Solution {
  stableMountains(height, threshold) { return solve(height, threshold); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, stableMountains };
