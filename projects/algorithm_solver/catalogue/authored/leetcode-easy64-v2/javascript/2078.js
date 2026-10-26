'use strict';

// 2078. Two Furthest Houses With Different Colors (Easy).
// Specification: https://leetcode.com/problems/two-furthest-houses-with-different-colors/description/
// O(n) time, O(1) space; an optimal pair can use an endpoint.
function solve(colors) {
  const last = colors.length - 1;
  let result = 0;
  for (let index = 0; index <= last; index++) {
    if (colors[index] !== colors[0]) result = Math.max(result, index);
    if (colors[index] !== colors[last]) result = Math.max(result, last - index);
  }
  return result;
}

const maxDistance = solve;
class Solution {
  maxDistance(colors) { return solve(colors); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxDistance };
