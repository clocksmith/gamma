'use strict';

// 2874. Maximum Value of an Ordered Triplet II: carry the best earlier value and earlier ordered difference before scoring each endpoint.
// O(n) time and O(1) auxiliary space on the positive integer domain; inputs are read-only.
function solve(nums) {
  let largest = nums[0];
  let difference = 0;
  let best = 0;
  for (let index = 1; index < nums.length; index += 1) {
    const value = nums[index];
    best = Math.max(best, difference * value);
    difference = Math.max(difference, largest - value);
    largest = Math.max(largest, value);
  }
  return best;
}

const maximumTripletValue = solve;
class Solution {
  maximumTripletValue(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximumTripletValue };
