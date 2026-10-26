'use strict';

// 1664. Ways to Make a Fair Array: compare prefix totals with parity-flipped suffix totals after each deletion.
// O(n) time and O(1) auxiliary space; inputs are read-only.
function solve(nums) {
  let rightEven = 0;
  let rightOdd = 0;
  for (let index = 0; index < nums.length; index += 1) {
    if (index % 2 === 0) rightEven += nums[index];
    else rightOdd += nums[index];
  }
  let leftEven = 0;
  let leftOdd = 0;
  let answer = 0;
  for (let index = 0; index < nums.length; index += 1) {
    if (index % 2 === 0) rightEven -= nums[index];
    else rightOdd -= nums[index];
    if (leftEven + rightOdd === leftOdd + rightEven) answer += 1;
    if (index % 2 === 0) leftEven += nums[index];
    else leftOdd += nums[index];
  }
  return answer;
}

const waysToMakeFair = solve;
class Solution {
  waysToMakeFair(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, waysToMakeFair };
