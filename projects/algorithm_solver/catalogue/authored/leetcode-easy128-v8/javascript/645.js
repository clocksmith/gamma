'use strict';

// 645. Set Mismatch (Easy).
// Specification: https://leetcode.com/problems/set-mismatch/description/
// O(n) time and space; count occurrences and return duplicate then missing.
function solve(nums) {
  const counts = new Array(nums.length + 1).fill(0);
  for (const value of nums) counts[value]++;
  let duplicate = 0;
  let missing = 0;
  for (let value = 1; value <= nums.length; value++) {
    if (counts[value] === 2) duplicate = value;
    else if (counts[value] === 0) missing = value;
  }
  return [duplicate, missing];
}

const findErrorNums = solve;
class Solution {
  findErrorNums(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findErrorNums };
