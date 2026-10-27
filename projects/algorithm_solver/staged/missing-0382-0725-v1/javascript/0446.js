'use strict';

// 446. Arithmetic Slices II - Subsequence. Count length-at-least-two subsequences by endpoint and exact difference.

function solve(nums) {
  const ending = nums.map(() => new Map());
  let answer = 0;
  for (let i = 0; i < nums.length; i += 1) {
    for (let j = 0; j < i; j += 1) {
      const difference = nums[i] - nums[j], count = ending[j].get(difference) || 0;
      answer += count;
      ending[i].set(difference, (ending[i].get(difference) || 0) + count + 1);
    }
  }
  return answer;
}

const numberOfArithmeticSlices = solve;
class Solution {
  numberOfArithmeticSlices(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, numberOfArithmeticSlices };
