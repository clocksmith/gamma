'use strict';

// 624. Maximum Distance in Arrays (Medium).
// Specification: https://leetcode.com/problems/maximum-distance-in-arrays/description/
function solve(arrays) {
  let smallest = arrays[0][0]; let largest = arrays[0][arrays[0].length - 1];
  let best = 0;
  for (let i = 1; i < arrays.length; i++) {
    const current = arrays[i];
    best = Math.max(best, Math.abs(current[current.length - 1] - smallest), Math.abs(current[0] - largest));
    smallest = Math.min(smallest, current[0]);
    largest = Math.max(largest, current[current.length - 1]);
  }
  return best;
}
const maxDistance = solve;
class Solution { maxDistance(arrays) { return solve(arrays); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxDistance };
