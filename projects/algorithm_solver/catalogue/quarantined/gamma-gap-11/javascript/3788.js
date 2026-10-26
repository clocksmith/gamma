'use strict';

// 3788. Maximum Score of a Split.
// O(n) time and O(1) auxiliary space; inputs are preserved.
function solve(nums) {
  let leftSum = 0;
  for (let index = 0; index + 1 < nums.length; index += 1) leftSum += nums[index];
  let suffixMinimum = nums[nums.length - 1];
  let answer = leftSum - suffixMinimum;
  for (let index = nums.length - 2; index > 0; index -= 1) {
    leftSum -= nums[index];
    suffixMinimum = Math.min(suffixMinimum, nums[index]);
    answer = Math.max(answer, leftSum - suffixMinimum);
  }
  return answer;
}

const maximumScore = solve;
class Solution {
  maximumScore(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximumScore };
