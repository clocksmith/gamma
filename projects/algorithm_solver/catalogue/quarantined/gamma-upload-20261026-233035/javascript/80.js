'use strict';
// 80. Remove Duplicates from Sorted Array II.
function solve(nums) {
  let write = 0;
  for (const value of nums) {
    if (write < 2 || nums[write - 2] !== value) { nums[write] = value; write += 1; }
  }
  return write;
}
const removeDuplicates = solve;
class Solution { removeDuplicates(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, removeDuplicates };
