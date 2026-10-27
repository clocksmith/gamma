'use strict';
// 27. Remove Element.
function solve(nums, val) {
  let write = 0;
  for (const value of nums) {
    if (value !== val) { nums[write] = value; write += 1; }
  }
  return write;
}
const removeElement = solve;
class Solution { removeElement(nums, val) { return solve(nums, val); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, removeElement };
