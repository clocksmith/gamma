'use strict';

// 3069. Distribute Elements Into Two Arrays I (Easy).
// Specification: https://leetcode.com/problems/distribute-elements-into-two-arrays-i/description/
// O(n) time and space; return a fresh concatenation and preserve nums.
function solve(nums) {
  const first = [nums[0]];
  const second = [nums[1]];
  for (let index = 2; index < nums.length; index++) {
    if (first[first.length - 1] > second[second.length - 1]) first.push(nums[index]);
    else second.push(nums[index]);
  }
  return first.concat(second);
}

const resultArray = solve;
class Solution {
  resultArray(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, resultArray };
