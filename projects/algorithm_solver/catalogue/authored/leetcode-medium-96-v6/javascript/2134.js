'use strict';

// 2134. Minimum Swaps to Group All 1's Together II: maximize ones in a circular window whose width is the total one count.
// O(n) time and O(1) auxiliary space; inputs are read-only.
function solve(nums) {
  let width = 0;
  for (const value of nums) width += value;
  if (width <= 1) return 0;
  let inside = 0;
  for (let index = 0; index < width; index += 1) inside += nums[index];
  let best = inside;
  for (let start = 1; start < nums.length; start += 1) {
    inside -= nums[start - 1];
    inside += nums[(start + width - 1) % nums.length];
    best = Math.max(best, inside);
  }
  return width - best;
}

const minSwaps = solve;
class Solution {
  minSwaps(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minSwaps };
