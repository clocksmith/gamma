'use strict';
// 283. Move Zeroes.
function solve(nums) {
  let write = 0;
  for (const value of nums) if (value !== 0) nums[write++] = value;
  while (write < nums.length) nums[write++] = 0;
}
const moveZeroes = solve;
class Solution { moveZeroes(nums) { solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, moveZeroes };
