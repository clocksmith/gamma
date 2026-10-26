'use strict';

// 1980. Find Unique Binary String: differ from each input string at its own diagonal position.
// O(n) time and O(n) output construction space; inputs are read-only.
function solve(nums) {
  const result = [];
  for (let index = 0; index < nums.length; index += 1) {
    result.push(nums[index][index] === '0' ? '1' : '0');
  }
  return result.join('');
}

const findDifferentBinaryString = solve;
class Solution {
  findDifferentBinaryString(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findDifferentBinaryString };
