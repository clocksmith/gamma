'use strict';

// 565. Array Nesting (Medium).
// Specification: https://leetcode.com/problems/array-nesting/description/
function solve(nums) {
  const visited = new Array(nums.length).fill(false);
  let best = 0;
  for (let start = 0; start < nums.length; start++) {
    if (visited[start]) continue;
    let length = 0; let current = start;
    while (!visited[current]) { visited[current] = true; current = nums[current]; length++; }
    best = Math.max(best, length);
  }
  return best;
}
const arrayNesting = solve;
class Solution { arrayNesting(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, arrayNesting };
