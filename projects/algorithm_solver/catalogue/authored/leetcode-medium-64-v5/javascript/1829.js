'use strict';

// 1829. Maximum XOR for Each Query: complement the active prefix XOR within the permitted bit mask.
// O(n) time and O(n) output space with O(1) auxiliary space; inputs are read-only.
function solve(nums, maximumBit) {
  let combined = 0;
  for (const value of nums) combined ^= value;
  const mask = 2 ** maximumBit - 1;
  const result = [];
  for (let index = nums.length - 1; index >= 0; index -= 1) {
    result.push(mask ^ combined);
    combined ^= nums[index];
  }
  return result;
}

const getMaximumXor = solve;
class Solution {
  getMaximumXor(nums, maximumBit) { return solve(nums, maximumBit); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, getMaximumXor };
