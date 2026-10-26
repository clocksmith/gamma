'use strict';

// 3516. Find Closest Person (Easy).
// Specification: https://leetcode.com/problems/find-closest-person/description/
// O(1) time and space; return zero when the two distances are equal.
function solve(x, y, z) {
  const firstDistance = Math.abs(x - z);
  const secondDistance = Math.abs(y - z);
  if (firstDistance < secondDistance) return 1;
  if (secondDistance < firstDistance) return 2;
  return 0;
}

const findClosest = solve;
class Solution {
  findClosest(x, y, z) { return solve(x, y, z); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findClosest };
