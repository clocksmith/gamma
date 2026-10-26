'use strict';

// 2552. Count Increasing Quadruplets. Maintain the number of valid three-index prefixes for each high middle index; O(n^2) time and O(n) space. Inputs are preserved.

function solve(nums) {
  const triples = Array(nums.length).fill(0);
  let answer = 0;
  for (let last = 0; last < nums.length; last += 1) {
    const value = nums[last];
    let smaller = 0;
    for (let middle = 0; middle < last; middle += 1) {
      if (nums[middle] < value) {
        answer += triples[middle];
        smaller += 1;
      } else if (nums[middle] > value) {
        triples[middle] += smaller;
      }
    }
  }
  return answer;
}

const countQuadruplets = solve;
class Solution {
  countQuadruplets(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countQuadruplets };
