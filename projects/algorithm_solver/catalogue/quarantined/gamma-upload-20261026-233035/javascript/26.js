'use strict';
// 26. Remove Duplicates from Sorted Array.
function solve(nums) {
  let write = 0;
  for (const value of nums) {
    if (write === 0 || nums[write - 1] !== value) {
      nums[write] = value;
      write += 1;
    }
  }
  return write;
}
const removeDuplicates = solve;
class Solution { removeDuplicates(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, removeDuplicates };
