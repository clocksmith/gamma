'use strict';
// 368. Largest Divisible Subset.
function solve(nums) {
  if (nums.length === 0) return [];
  nums = nums.slice().sort((a, b) => a - b);
  const lengths = Array(nums.length).fill(1); const previous = Array(nums.length).fill(-1); let best = 0;
  for (let index = 0; index < nums.length; index += 1) {
    for (let prior = 0; prior < index; prior += 1) {
      if (nums[index] % nums[prior] === 0 && lengths[prior] + 1 > lengths[index]) {
        lengths[index] = lengths[prior] + 1; previous[index] = prior;
      }
    }
    if (lengths[index] > lengths[best]) best = index;
  }
  const result = [];
  while (best >= 0) { result.push(nums[best]); best = previous[best]; }
  return result.reverse();
}
const largestDivisibleSubset = solve;
class Solution { largestDivisibleSubset(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, largestDivisibleSubset };
