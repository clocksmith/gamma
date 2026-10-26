'use strict';

// 1313. Decompress Run-Length Encoded List (Easy).
// Specification: https://leetcode.com/problems/decompress-run-length-encoded-list/description/
// O(n + output length) time, O(output length) space; preserve nums.
function solve(nums) {
  const result = [];
  for (let index = 0; index < nums.length; index += 2) {
    const frequency = nums[index];
    const value = nums[index + 1];
    for (let count = 0; count < frequency; count++) result.push(value);
  }
  return result;
}

const decompressRLElist = solve;
class Solution {
  decompressRLElist(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, decompressRLElist };
