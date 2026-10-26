'use strict';

// 1968. Array With Elements Not Equal to Average of Neighbors: turn a sorted copy into alternating strict peaks and valleys.
// O(n * log(n + 1)) time and O(n) space; inputs are read-only.
function solve(nums) {
  const result = nums.slice().sort((a, b) => a - b);
  for (let index = 1; index + 1 < result.length; index += 2) {
    [result[index], result[index + 1]] = [result[index + 1], result[index]];
  }
  return result;
}

const rearrangeArray = solve;
class Solution {
  rearrangeArray(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, rearrangeArray };
