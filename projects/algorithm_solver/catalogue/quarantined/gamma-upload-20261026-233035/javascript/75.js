'use strict';
// 75. Sort Colors.
function solve(nums) {
  let low = 0;
  let current = 0;
  let high = nums.length - 1;
  while (current <= high) {
    if (nums[current] === 0) {
      [nums[low], nums[current]] = [nums[current], nums[low]];
      low += 1; current += 1;
    } else if (nums[current] === 2) {
      [nums[current], nums[high]] = [nums[high], nums[current]];
      high -= 1;
    } else current += 1;
  }
}
const sortColors = solve;
class Solution { sortColors(nums) { solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, sortColors };
