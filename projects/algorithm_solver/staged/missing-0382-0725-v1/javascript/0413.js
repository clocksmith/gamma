'use strict';

// 413. Arithmetic Slices.

function solve(nums) {
  let answer = 0, ending = 0;
  for (let i = 2; i < nums.length; i += 1) {
    ending = nums[i] - nums[i - 1] === nums[i - 1] - nums[i - 2] ? ending + 1 : 0;
    answer += ending;
  }
  return answer;
}

const numberOfArithmeticSlices = solve;
class Solution {
  numberOfArithmeticSlices(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, numberOfArithmeticSlices };
