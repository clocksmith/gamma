'use strict';

// 3740. Minimum Distance Between Three Equal Elements I (Easy).
// Specification: https://leetcode.com/problems/minimum-distance-between-three-equal-elements-i/description/
// O(n) expected time and space; consecutive occurrences minimize twice the endpoint span.
function solve(nums) {
  const positions = new Map();
  let result = Infinity;
  for (let index = 0; index < nums.length; index++) {
    const value = nums[index];
    if (!positions.has(value)) positions.set(value, []);
    const occurrences = positions.get(value);
    occurrences.push(index);
    if (occurrences.length >= 3) {
      result = Math.min(result, 2 * (index - occurrences[occurrences.length - 3]));
    }
  }
  return result === Infinity ? -1 : result;
}

const minimumDistance = solve;
class Solution {
  minimumDistance(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumDistance };
